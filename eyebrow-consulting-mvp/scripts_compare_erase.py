from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
SRC = ROOT / 'eyebrow-consulting-mvp/web/sample.jpg'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
OUT_DIR = ROOT / 'out/eyebrow_alg_compare'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_landmarks():
    mp_image = mp.Image.create_from_file(str(SRC))
    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL)),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    landmarker = vision.FaceLandmarker.create_from_options(options)
    result = landmarker.detect(mp_image)
    if not result.face_landmarks:
        raise RuntimeError('No face landmarks detected')
    return result.face_landmarks[0]


def pts_from_indices(landmarks, indices, w, h):
    return np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in indices], dtype=np.float32)


def unique_indices(edges):
    return sorted({c.start for c in edges} | {c.end for c in edges})


def eyebrow_masks(img_bgr, landmarks):
    h, w = img_bgr.shape[:2]
    conn = vision.FaceLandmarksConnections
    left_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYEBROW)
    right_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYEBROW)
    left = pts_from_indices(landmarks, left_idx, w, h)
    right = pts_from_indices(landmarks, right_idx, w, h)

    mask = np.zeros((h, w), dtype=np.uint8)
    debug = img_bgr.copy()

    boxes = []
    for pts, color in [(left, (0,0,255)), (right, (255,0,0))]:
        hull = cv2.convexHull(pts.astype(np.int32))
        x, y, bw, bh = cv2.boundingRect(hull)
        boxes.append((x, y, bw, bh))

        # compact mask: widen mostly vertically a bit, not huge box growth
        cx = x + bw / 2
        cy = y + bh / 2
        expanded = []
        for px, py in pts:
            ex = cx + (px - cx) * 1.05
            ey = cy + (py - cy) * 1.55 + bh * 0.18
            expanded.append([ex, ey])
        expanded = np.array(expanded, dtype=np.int32)
        poly = cv2.convexHull(expanded)
        cv2.fillConvexPoly(mask, poly, 255)

        cv2.polylines(debug, [hull], True, color, 2)
        cv2.rectangle(debug, (x,y), (x+bw, y+bh), color, 2)
        for px, py in pts.astype(np.int32):
            cv2.circle(debug, (px, py), 2, (0,255,0), -1)

    # feather mask a bit for blend
    mask = cv2.GaussianBlur(mask, (0,0), 2.0)
    return mask, debug, boxes


def sample_skin_patch(img, box, side='left'):
    h, w = img.shape[:2]
    x, y, bw, bh = box
    # cheek-biased patch below and slightly outward from brow
    if side == 'left':
        rx = int(max(0, x - 0.10*bw))
    else:
        rx = int(min(w-1, x + 0.10*bw))
    ry = int(min(h-1, y + 1.6*bh))
    rw = int(max(12, 1.5*bw))
    rh = int(max(12, 1.1*bh))
    rx = min(rx, w-rw)
    ry = min(ry, h-rh)
    return img[ry:ry+rh, rx:rx+rw].copy()


def robust_skin_color(patch):
    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    sel = (L > np.percentile(L, 25)) & (L < np.percentile(L, 85))
    if sel.sum() < 20:
        sel = np.ones_like(L, dtype=bool)
    vals = patch[sel]
    med = np.median(vals, axis=0)
    return med.astype(np.float32)


def hist_match_gray(src_vals, ref_vals):
    src = np.clip(src_vals, 0, 255).astype(np.uint8)
    ref = np.clip(ref_vals, 0, 255).astype(np.uint8)
    src_hist, _ = np.histogram(src.flatten(), 256, [0,256], density=True)
    ref_hist, _ = np.histogram(ref.flatten(), 256, [0,256], density=True)
    src_cdf = np.cumsum(src_hist)
    ref_cdf = np.cumsum(ref_hist)
    lut = np.interp(src_cdf, ref_cdf, np.arange(256))
    return lut[src].astype(np.uint8)


def algo_current_like(img, mask):
    blurred = cv2.GaussianBlur(img, (0,0), 7)
    skin = cv2.blur(img, (25,25))
    blend = cv2.addWeighted(blurred, 0.45, skin, 0.55, 0)
    alpha = (mask.astype(np.float32)/255.0)[...,None] * 0.95
    out = img.astype(np.float32)*(1-alpha) + blend.astype(np.float32)*alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def algo_inpaint_hist(img, mask, boxes):
    out = cv2.inpaint(img, (mask>32).astype(np.uint8)*255, 3, cv2.INPAINT_TELEA)
    alpha = (mask.astype(np.float32)/255.0)[...,None]
    for i, box in enumerate(boxes):
        side = 'left' if i == 0 else 'right'
        patch = sample_skin_patch(img, box, side)
        target = robust_skin_color(patch)
        x, y, bw, bh = box
        pad = int(max(8, bh*1.2))
        x0, y0 = max(0, x-pad), max(0, y-pad)
        x1, y1 = min(img.shape[1], x+bw+pad), min(img.shape[0], y+bh+pad)
        roi = out[y0:y1, x0:x1].copy()
        roi_mask = alpha[y0:y1, x0:x1]
        # LAB transfer on masked area toward cheek-skin medians
        roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).astype(np.float32)
        tgt_lab = cv2.cvtColor(np.uint8([[target]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
        mean_lab = np.array([np.mean(roi_lab[...,c][roi_mask[...,0] > 0.15]) if np.any(roi_mask[...,0] > 0.15) else roi_lab[...,c].mean() for c in range(3)])
        shift = (tgt_lab - mean_lab)
        roi_lab[...,0] += shift[0] * roi_mask[...,0] * 0.55
        roi_lab[...,1] += shift[1] * roi_mask[...,0] * 0.8
        roi_lab[...,2] += shift[2] * roi_mask[...,0] * 0.8
        roi_lab = np.clip(roi_lab, 0, 255).astype(np.uint8)
        roi_bgr = cv2.cvtColor(roi_lab, cv2.COLOR_LAB2BGR)
        # suppress residual dark hair using gray histogram toward patch
        gray_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        matched = hist_match_gray(gray_roi[roi_mask[...,0] > 0.15], gray_ref.flatten())
        gray_new = gray_roi.copy()
        gray_new[roi_mask[...,0] > 0.15] = matched
        lift = np.clip(gray_new.astype(np.float32) - gray_roi.astype(np.float32), 0, 28)
        roi_bgr = np.clip(roi_bgr.astype(np.float32) + lift[...,None]*0.35, 0, 255).astype(np.uint8)
        # edge-preserving smooth for skin texture coherence
        roi_bgr = cv2.bilateralFilter(roi_bgr, 7, 20, 20)
        out[y0:y1, x0:x1] = np.where((roi_mask>0.05), roi_bgr, out[y0:y1, x0:x1])
    return out


def algo_seamless_clone(img, mask, boxes):
    base = cv2.inpaint(img, (mask>32).astype(np.uint8)*255, 3, cv2.INPAINT_NS)
    out = base.copy()
    for i, box in enumerate(boxes):
        side = 'left' if i == 0 else 'right'
        patch = sample_skin_patch(img, box, side)
        x, y, bw, bh = box
        dst_w = max(12, int(bw * 1.35))
        dst_h = max(12, int(bh * 1.8))
        patch_r = cv2.resize(patch, (dst_w, dst_h), interpolation=cv2.INTER_CUBIC)
        patch_mask = np.full((dst_h, dst_w), 255, dtype=np.uint8)
        center = (int(x + bw/2), int(y + bh*0.95))
        try:
            out = cv2.seamlessClone(patch_r, out, patch_mask, center, cv2.NORMAL_CLONE)
        except cv2.error:
            pass
    # confine to eyebrow mask blend so clone doesn't spill much
    alpha = (mask.astype(np.float32)/255.0)[...,None] * 0.85
    out = img.astype(np.float32)*(1-alpha) + out.astype(np.float32)*alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0,0), (out.shape[1], 40), (20,20,20), -1)
    cv2.putText(out, text, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
    return out


def main():
    img = cv2.imread(str(SRC))
    landmarks = load_landmarks()
    mask, debug, boxes = eyebrow_masks(img, landmarks)
    cv2.imwrite(str(OUT_DIR / 'debug_landmarks_boxes.png'), debug)
    cv2.imwrite(str(OUT_DIR / 'debug_mask.png'), mask)

    a = algo_current_like(img, mask)
    b = algo_inpaint_hist(img, mask, boxes)
    c = algo_seamless_clone(img, mask, boxes)

    cv2.imwrite(str(OUT_DIR / 'erase_current_like.png'), a)
    cv2.imwrite(str(OUT_DIR / 'erase_inpaint_hist.png'), b)
    cv2.imwrite(str(OUT_DIR / 'erase_seamless_clone.png'), c)

    tiles = [
        label(img, 'original'),
        label(debug, 'mediapipe landmarks + brow boxes'),
        label(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), 'erase mask'),
        label(a, 'A current-like blur/fill'),
        label(b, 'B inpaint + histogram/LAB skin match'),
        label(c, 'C seamless clone skin patch'),
    ]
    top = np.hstack(tiles[:3])
    bot = np.hstack(tiles[3:])
    grid = np.vstack([top, bot])
    cv2.imwrite(str(OUT_DIR / 'comparison_grid.png'), grid)
    print({'out_dir': str(OUT_DIR), 'boxes': boxes})

if __name__ == '__main__':
    main()
