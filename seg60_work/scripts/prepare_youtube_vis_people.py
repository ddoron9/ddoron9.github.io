#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import random
import zipfile
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageDraw

PERSON_CATEGORY_ID = 26


def decode_uncompressed_rle(counts: list[int], height: int, width: int) -> np.ndarray:
    total = height * width
    flat = np.zeros(total, dtype=np.uint8)
    idx = 0
    value = 0
    for run in counts:
        run = int(run)
        if run <= 0:
            value = 1 - value
            continue
        end = min(idx + run, total)
        if value == 1:
            flat[idx:end] = 1
        idx = end
        value = 1 - value
        if idx >= total:
            break
    return flat.reshape((width, height), order='F').T


def segmentation_to_mask(segmentation, height: int, width: int) -> np.ndarray:
    if segmentation is None:
        return np.zeros((height, width), dtype=np.uint8)
    if isinstance(segmentation, dict):
        counts = segmentation.get('counts')
        if isinstance(counts, list):
            return decode_uncompressed_rle(counts, height, width)
        raise ValueError('compressed RLE string is not supported in this script')
    if isinstance(segmentation, list):
        mask = np.zeros((height, width), dtype=np.uint8)
        polys = []
        for poly in segmentation:
            arr = np.asarray(poly, dtype=np.float32).reshape(-1, 2)
            if len(arr) >= 3:
                polys.append(np.round(arr).astype(np.int32))
        if polys:
            cv2.fillPoly(mask, polys, 1)
        return mask
    raise TypeError(f'unsupported segmentation type: {type(segmentation)}')


def read_json_from_zip(zip_path: Path, member_name: str) -> dict:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member_name) as f:
            return json.load(f)


def read_nested_json(outer_zip: Path, inner_zip_name: str, json_name: str) -> dict:
    with zipfile.ZipFile(outer_zip) as outer:
        inner_data = outer.read(inner_zip_name)
    with zipfile.ZipFile(io.BytesIO(inner_data)) as inner:
        with inner.open(json_name) as f:
            return json.load(f)


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def write_image_from_zip(zip_file: zipfile.ZipFile, member: str, out_path: Path):
    ensure_parent(out_path)
    if out_path.exists():
        return
    with zip_file.open(member) as src, out_path.open('wb') as dst:
        dst.write(src.read())


def build_frame_union_masks(meta: dict, prefix: str):
    videos = {v['id']: v for v in meta['videos']}
    frame_masks: dict[tuple[int, int], np.ndarray] = {}
    frame_instance_counts: dict[tuple[int, int], int] = defaultdict(int)
    person_annotations = [a for a in meta.get('annotations', []) if a.get('category_id') == PERSON_CATEGORY_ID]
    for ann in person_annotations:
        vid = videos[ann['video_id']]
        height = int(ann.get('height') or vid['height'])
        width = int(ann.get('width') or vid['width'])
        for frame_idx, seg in enumerate(ann['segmentations']):
            if seg is None:
                continue
            key = (ann['video_id'], frame_idx)
            if key not in frame_masks:
                frame_masks[key] = np.zeros((height, width), dtype=np.uint8)
            mask = segmentation_to_mask(seg, height, width)
            if mask.any():
                frame_masks[key] |= mask.astype(np.uint8)
                frame_instance_counts[key] += 1
    return videos, frame_masks, frame_instance_counts, person_annotations


def write_manifest(rows: list[dict], path: Path):
    ensure_parent(path)
    fieldnames = [
        'sample_id', 'dataset', 'scene_id', 'clip_id', 'frame_id', 'image_path', 'mask_path', 'split',
        'tags', 'width', 'height', 'is_video', 'source_weight', 'notes'
    ]
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_qc_panel(samples: list[dict], out_path: Path, title: str = 'youtube_vis_people_qc'):
    ensure_parent(out_path)
    picked = samples[:10]
    if not picked:
        return
    cell_w = 320
    cell_h = 180
    title_h = 24
    cols = 3
    rows = len(picked)
    canvas = Image.new('RGB', (cols * cell_w, rows * (cell_h + title_h)), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    for row_idx, sample in enumerate(picked):
        image = Image.open(sample['image_path']).convert('RGB')
        mask = Image.open(sample['mask_path']).convert('L')
        mask_rgb = ImageOps.colorize(mask, black=(0, 0, 0), white=(255, 255, 255)).convert('RGB')
        arr = np.array(image)
        marr = np.array(mask) > 0
        overlay = arr.copy()
        overlay[marr] = (0.55 * overlay[marr] + 0.45 * np.array([255, 64, 64])).astype(np.uint8)
        overlay_img = Image.fromarray(overlay)
        tiles = [image, mask_rgb, overlay_img]
        for col_idx, tile in enumerate(tiles):
            tile = ImageOps.contain(tile, (cell_w, cell_h))
            x = col_idx * cell_w + (cell_w - tile.width) // 2
            y = row_idx * (cell_h + title_h) + title_h + (cell_h - tile.height) // 2
            canvas.paste(tile, (x, y))
        label = f"{sample['clip_id']}/{sample['frame_id']} split={sample['split']}"
        draw.text((8, row_idx * (cell_h + title_h) + 4), label, fill=(235, 235, 235))
    canvas.save(out_path, quality=92)


def main():
    ap = argparse.ArgumentParser(description='Prepare person-only YouTube-VIS dataset for seg60')
    ap.add_argument('--train-zip', required=True)
    ap.add_argument('--valid-zip', required=True)
    ap.add_argument('--support-zip', required=True)
    ap.add_argument('--out-root', required=True)
    ap.add_argument('--train-frame-stride', type=int, default=2)
    ap.add_argument('--val-frame-stride', type=int, default=1)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    out_root = Path(args.out_root).resolve()
    images_root = out_root / 'images'
    masks_root = out_root / 'masks'
    manifests_root = out_root / 'manifests'
    reports_root = out_root / 'reports'
    for p in [images_root, masks_root, manifests_root, reports_root]:
        p.mkdir(parents=True, exist_ok=True)

    train_meta = read_json_from_zip(Path(args.train_zip), 'train/instances.json')
    val_meta = read_nested_json(Path(args.support_zip), 'validation_gt.zip', 'gt.json')

    summary = {
        'train_zip': str(Path(args.train_zip).resolve()),
        'valid_zip': str(Path(args.valid_zip).resolve()),
        'support_zip': str(Path(args.support_zip).resolve()),
        'person_category_id': PERSON_CATEGORY_ID,
        'train_frame_stride': args.train_frame_stride,
        'val_frame_stride': args.val_frame_stride,
    }

    outputs = {}
    all_rows_for_qc = []

    split_specs = [
        ('train', Path(args.train_zip), 'train', train_meta, args.train_frame_stride),
        ('val', Path(args.valid_zip), 'valid', val_meta, args.val_frame_stride),
    ]

    for split_name, zip_path, zip_prefix, meta, stride in split_specs:
        videos, frame_masks, frame_instance_counts, person_annotations = build_frame_union_masks(meta, zip_prefix)
        rows = []
        kept_frames = 0
        with zipfile.ZipFile(zip_path) as zf:
            for (video_id, frame_idx), mask in sorted(frame_masks.items()):
                if frame_idx % max(stride, 1) != 0:
                    continue
                video = videos[video_id]
                rel_name = video['file_names'][frame_idx]
                zip_member = f'{zip_prefix}/JPEGImages/{rel_name}'
                clip_id = Path(rel_name).parent.name
                frame_id = Path(rel_name).stem
                image_out = images_root / split_name / clip_id / f'{frame_id}.jpg'
                mask_out = masks_root / split_name / clip_id / f'{frame_id}.png'
                write_image_from_zip(zf, zip_member, image_out)
                ensure_parent(mask_out)
                Image.fromarray((mask > 0).astype(np.uint8) * 255).save(mask_out)
                sample_id = f'youtube_vis_person_{split_name}_{kept_frames + 1:06d}'
                row = {
                    'sample_id': sample_id,
                    'dataset': 'youtube_vis_person',
                    'scene_id': clip_id,
                    'clip_id': clip_id,
                    'frame_id': frame_id,
                    'image_path': str(image_out),
                    'mask_path': str(mask_out),
                    'split': split_name,
                    'tags': f'youtube_vis|person|official|{split_name}',
                    'width': int(video['width']),
                    'height': int(video['height']),
                    'is_video': 'true',
                    'source_weight': 1.0,
                    'notes': f"video_id={video_id};frame_idx={frame_idx};person_instances={frame_instance_counts[(video_id, frame_idx)]};frame_stride={stride}",
                }
                rows.append(row)
                all_rows_for_qc.append(row)
                kept_frames += 1
        manifest_path = manifests_root / f'youtube_vis_person_{split_name}.csv'
        write_manifest(rows, manifest_path)
        outputs[split_name] = {
            'manifest_path': str(manifest_path),
            'rows': len(rows),
            'person_annotations': len(person_annotations),
            'person_videos': len({a['video_id'] for a in person_annotations}),
            'frames_with_person_before_stride': len(frame_masks),
            'images_dir': str(images_root / split_name),
            'masks_dir': str(masks_root / split_name),
        }

    qc_candidates = [r for r in all_rows_for_qc if r['split'] == 'val']
    if len(qc_candidates) < 10:
        qc_candidates = all_rows_for_qc
    qc_candidates = sorted(qc_candidates, key=lambda r: (r['clip_id'], r['frame_id']))
    if len(qc_candidates) > 10:
        step = max(1, len(qc_candidates) // 10)
        qc_candidates = [qc_candidates[i] for i in range(0, len(qc_candidates), step)][:10]
    qc_path = reports_root / 'youtube_vis_person_qc_10panel.jpg'
    build_qc_panel(qc_candidates, qc_path)

    summary['outputs'] = outputs
    summary['qc_panel'] = str(qc_path)
    summary_path = reports_root / 'youtube_vis_person_summary.json'
    summary_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
