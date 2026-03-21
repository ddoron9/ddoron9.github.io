#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from ultralytics import YOLO


@dataclass
class FrameCandidate:
    sample_id: str
    source_id: str
    source_path: str
    license_tag: str
    source_kind: str
    scene_type: str
    frame_idx: int
    timestamp_sec: float
    width: int
    height: int
    image_path: str
    hash16: str
    person_instances: int
    person_score_mean: float
    fg_ratio: float
    mask_path: str
    overlay_path: str
    keep_reason: str = ""
    reject_reason: str = ""


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ahash16(image_bgr: np.ndarray, size: int = 16) -> str:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    bits = small >= small.mean()
    packed = np.packbits(bits.reshape(-1).astype(np.uint8))
    return packed.tobytes().hex()


def hamming_hex(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def write_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255)).save(path)


def write_overlay(image_bgr: np.ndarray, mask: np.ndarray, path: Path) -> None:
    overlay = image_bgr.copy()
    overlay[mask > 0] = (0.35 * overlay[mask > 0] + 0.65 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imwrite(str(path), overlay)


def pick_person_mask(result, min_conf: float) -> tuple[np.ndarray, int, float]:
    orig_h, orig_w = result.orig_shape[:2]
    if result.masks is None or result.boxes is None:
        return np.zeros((orig_h, orig_w), dtype=bool), 0, 0.0
    cls = result.boxes.cls.detach().cpu().numpy().astype(int)
    conf = result.boxes.conf.detach().cpu().numpy()
    data = result.masks.data.detach().cpu().numpy()
    keep = np.where((cls == 0) & (conf >= min_conf))[0]
    if keep.size == 0:
        return np.zeros((orig_h, orig_w), dtype=bool), 0, 0.0
    mask = data[keep].max(axis=0)
    if mask.shape != (orig_h, orig_w):
        mask = cv2.resize(mask.astype(np.float32), (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
    mask = mask > 0.5
    return mask, int(keep.size), float(conf[keep].mean())


def save_csv(rows: list[dict[str, Any]], path: Path) -> None:
    ensure_dir(path.parent)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_panel(items: list[FrameCandidate], out_path: Path, title: str) -> None:
    cols = 3
    rows = len(items)
    fig, axes = plt.subplots(rows, cols, figsize=(12, 4 * rows))
    if rows == 1:
        axes = np.array([axes])
    for r, item in enumerate(items):
        img = cv2.cvtColor(cv2.imread(item.image_path), cv2.COLOR_BGR2RGB)
        mask = np.array(Image.open(item.mask_path))
        overlay = cv2.cvtColor(cv2.imread(item.overlay_path), cv2.COLOR_BGR2RGB)
        for c, arr, name in [(0, img, 'image'), (1, mask, 'mask'), (2, overlay, 'overlay')]:
            ax = axes[r, c]
            ax.imshow(arr, cmap='gray' if name == 'mask' else None)
            ax.axis('off')
            if c == 0:
                ax.set_title(f"{item.sample_id}\n{item.source_id} t={item.timestamp_sec:.1f}s")
            else:
                ax.set_title(name)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches='tight')
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    cfg = json.loads(config_path.read_text())
    root = Path(cfg['output_root']).resolve()
    ensure_dir(root)
    image_dir = ensure_dir(root / 'images')
    mask_dir = ensure_dir(root / 'masks')
    overlay_dir = ensure_dir(root / 'overlays')
    qc_dir = ensure_dir(root / 'qc')
    manifest_dir = ensure_dir(root / 'manifests')

    model = YOLO(cfg.get('teacher_model', 'yolo11x-seg.pt'))
    min_conf = float(cfg.get('min_conf', 0.25))
    min_fg_ratio = float(cfg.get('min_fg_ratio', 0.01))
    max_fg_ratio = float(cfg.get('max_fg_ratio', 0.65))
    min_person_instances = int(cfg.get('min_person_instances', 1))
    extract_every_n = int(cfg.get('extract_every_n', 12))
    dedup_hamming = int(cfg.get('dedup_hamming', 8))
    max_keep = int(cfg.get('max_keep', 48))
    audit_count = int(cfg.get('audit_count', 10))
    imgsz = int(cfg.get('imgsz', 960))

    candidates: list[FrameCandidate] = []
    accepted_hashes: list[str] = []
    accepted: list[FrameCandidate] = []
    sample_counter = 0

    for source in cfg['sources']:
        source_path = Path(source['path']).expanduser().resolve()
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            continue
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        start = int(source.get('start_frame', 0))
        stop = int(source.get('end_frame', total if total > 0 else 10**9))
        for frame_idx in range(start, stop, extract_every_n):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            result = model.predict(frame, verbose=False, imgsz=imgsz, conf=min_conf, max_det=20)[0]
            mask, instances, score_mean = pick_person_mask(result, min_conf=min_conf)
            fg_ratio = float(mask.mean())
            h = ahash16(frame)
            sample_counter += 1
            sample_id = f"stage_people_{sample_counter:06d}"
            img_path = image_dir / f"{sample_id}.jpg"
            mask_path = mask_dir / f"{sample_id}.png"
            overlay_path = overlay_dir / f"{sample_id}.jpg"
            cv2.imwrite(str(img_path), frame)
            write_mask(mask, mask_path)
            write_overlay(frame, mask, overlay_path)
            item = FrameCandidate(
                sample_id=sample_id,
                source_id=source['source_id'],
                source_path=str(source_path),
                license_tag=source.get('license_tag', 'unknown'),
                source_kind=source.get('source_kind', 'local_video'),
                scene_type=source.get('scene_type', 'unknown'),
                frame_idx=frame_idx,
                timestamp_sec=frame_idx / fps,
                width=int(frame.shape[1]),
                height=int(frame.shape[0]),
                image_path=str(img_path),
                hash16=h,
                person_instances=instances,
                person_score_mean=round(score_mean, 5),
                fg_ratio=round(fg_ratio, 5),
                mask_path=str(mask_path),
                overlay_path=str(overlay_path),
            )
            if instances < min_person_instances:
                item.reject_reason = 'no_person'
            elif fg_ratio < min_fg_ratio:
                item.reject_reason = 'fg_too_small'
            elif fg_ratio > max_fg_ratio:
                item.reject_reason = 'fg_too_large'
            elif any(hamming_hex(h, prev) <= dedup_hamming for prev in accepted_hashes):
                item.reject_reason = 'near_duplicate'
            elif len(accepted) >= max_keep:
                item.reject_reason = 'max_keep_reached'
            else:
                item.keep_reason = 'accepted'
                accepted_hashes.append(h)
                accepted.append(item)
            candidates.append(item)
        cap.release()

    raw_rows = [asdict(x) for x in candidates]
    keep_rows = [asdict(x) for x in accepted]
    save_csv(raw_rows, manifest_dir / 'raw_candidates.csv')
    save_csv(keep_rows, manifest_dir / 'filtered_candidates.csv')

    seg_rows = []
    for i, item in enumerate(accepted):
        split = 'val' if (i % 5 == 0) else 'train'
        seg_rows.append({
            'sample_id': item.sample_id,
            'dataset': 'stage_broadcast_people_pseudo',
            'scene_id': item.source_id,
            'clip_id': item.source_id,
            'frame_id': f"{item.frame_idx:06d}",
            'image_path': item.image_path,
            'mask_path': item.mask_path,
            'split': split,
            'tags': '|'.join(['internal', 'pseudo_label', 'yolo11x_seg', item.scene_type, item.license_tag]),
            'width': item.width,
            'height': item.height,
            'is_video': 'true',
            'source_weight': 1.0,
            'notes': f"instances={item.person_instances};score_mean={item.person_score_mean};fg_ratio={item.fg_ratio};source={item.source_kind}",
        })
    save_csv(seg_rows, manifest_dir / 'seg60_manifest.csv')
    save_csv([r for r in seg_rows if r['split'] == 'train'], manifest_dir / 'seg60_train.csv')
    save_csv([r for r in seg_rows if r['split'] == 'val'], manifest_dir / 'seg60_val.csv')

    audit_items = accepted[:audit_count]
    if audit_items:
        make_panel(audit_items, qc_dir / 'audit_panel_10.png', 'Stage/Broadcast people pseudo-label audit')
        audit_rows = [asdict(x) for x in audit_items]
        (qc_dir / 'audit_panel_10.json').write_text(json.dumps(audit_rows, indent=2, ensure_ascii=False))

    summary = {
        'config_path': str(config_path),
        'output_root': str(root),
        'teacher_model': cfg.get('teacher_model', 'yolo11x-seg.pt'),
        'sources': cfg['sources'],
        'num_candidates': len(candidates),
        'num_kept': len(accepted),
        'num_train': sum(1 for r in seg_rows if r['split'] == 'train'),
        'num_val': sum(1 for r in seg_rows if r['split'] == 'val'),
        'audit_panel': str(qc_dir / 'audit_panel_10.png'),
        'manifests': {
            'raw_candidates': str(manifest_dir / 'raw_candidates.csv'),
            'filtered_candidates': str(manifest_dir / 'filtered_candidates.csv'),
            'seg60_manifest': str(manifest_dir / 'seg60_manifest.csv'),
            'seg60_train': str(manifest_dir / 'seg60_train.csv'),
            'seg60_val': str(manifest_dir / 'seg60_val.csv'),
        },
    }
    (root / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
