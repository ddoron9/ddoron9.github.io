from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
SRC = ROOT / 'eyebrow-consulting-mvp/web/sample.jpg'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
OUT_DIR = ROOT / 'out/eyebrow_alg_compare_rawpoly'
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


def unique_indices(edges):
    return sorted({c.start for c in edges} | {c.end for c in edges})


def pt_arr(landmarks, idxs, w, h):
    return np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idxs], dtype=np.float32)


def build_masks(img, landmarks):
    h, w = img.shape[:2]
    conn = vision.FaceLandmarksConnections
    left_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYEBROW)
    right_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYEBROW)
    groups = [pt_arr(landmarks, left_idx, w, h), pt_arr(landmarks, right_idx, w, h)]

    raw = np.zeros((h, w), np.uint8)
    soft = np.zeros((h, w), np.uint8)
    debug = img.copy()
    boxes = []

    for pts, color in [(groups[0], (0,0,255)), (groups[1], (255,0,0))]:
        hull = cv2.convexHull(pts.astype(np.int32))
        cv2.fillConvexPoly(raw, hull, 255)
        # tiny dilation only, not big box expansion
        small = cv2.dilate(raw if False else np.zeros_like(raw), np.ones((1,1), np.uint8))
        local = np.zeros_like(raw)
        cv2.fillConvexPoly(local, hull, 255)
        local = cv2.dilate(local, np.ones((3,3), np.uint8), iterations=1)
        local = cv2.GaussianBlur(local, (0,0), 1.2)
        soft = np.maximum(soft, local)

        x,y,bw,bh = cv2.boundingRect(hull)
        boxes.append((x,y,bw,bh))
        cv2.polylines(debug, [hull], True, color, 2)
        cv2.rectangle(debug, (x,y), (x+bw,y+bh), color, 1)
        for px, py in pts.astype(np.int32):
            cv2.circle(debug, (px, py), 2, (0,255,0), -1)

    return raw, soft, debug, boxes


def sample_skin_patch(img, box, side='left'):
    h, w = img.shape[:2]
    x, y, bw, bh = box
    rx = int(max(0, x - 0.1*bw)) if side == 'left' else int(min(w-1, x + 0.1*bw))
    ry = int(min(h-1, y + 1.5*bh))
    rw = int(max(12, 1.4*bw))
    rh = int(max(12, 1.0*bh))
    rx = min(rx, w-rw)
    ry = min(ry, h-rh)
    return img[ry:ry+rh, rx:rx+rw].copy()


def robust_skin_color(patch):
    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    L = lab[...,0]
    sel = (L > np.percentile(L, 25)) & (L < np.percentile(L, 85))
    vals = patch[sel] if np.any(sel) else patch.reshape(-1,3)
    return np.median(vals, axis=0).astype(np.float32)


def algo_rawpoly_inpaint_hist(img, soft_mask, boxes):
    out = cv2.inpaint(img, (soft_mask > 20).astype(np.uint8)*255, 2, cv2.INPAINT_TELEA)
    alpha = (soft_mask.astype(np.float32)/255.0)[...,None]
    for i, box in enumerate(boxes):
        side = 'left' if i == 0 else 'right'
        patch = sample_skin_patch(img, box, side)
        target = robust_skin_color(patch)
        x, y, bw, bh = box
        pad = int(max(4, bh*0.8))
        x0, y0 = max(0, x-pad), max(0, y-pad)
        x1, y1 = min(img.shape[1], x+bw+pad), min(img.shape[0], y+bh+pad)
        roi = out[y0:y1, x0:x1].copy()
        roi_mask = alpha[y0:y1, x0:x1][...,0]
        roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).astype(np.float32)
        tgt_lab = cv2.cvtColor(np.uint8([[target]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
        active = roi_mask > 0.08
        if np.any(active):
            mean_lab = np.array([roi_lab[...,c][active].mean() for c in range(3)])
            shift = tgt_lab - mean_lab
            roi_lab[...,0] += shift[0] * roi_mask * 0.35
            roi_lab[...,1] += shift[1] * roi_mask * 0.55
            roi_lab[...,2] += shift[2] * roi_mask * 0.55
        roi = cv2.cvtColor(np.clip(roi_lab,0,255).astype(np.uint8), cv2.COLOR_LAB2BGR)
        roi = cv2.bilateralFilter(roi, 5, 18, 18)
        out[y0:y1, x0:x1] = np.where(active[...,None], roi, out[y0:y1, x0:x1])
    return out


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0,0), (out.shape[1], 40), (20,20,20), -1)
    cv2.putText(out, text, (12,28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
    return out


def main():
    img = cv2.imread(str(SRC))
    landmarks = load_landmarks()
    raw, soft, debug, boxes = build_masks(img, landmarks)
    out = algo_rawpoly_inpaint_hist(img, soft, boxes)
    cv2.imwrite(str(OUT_DIR / 'debug_landmarks_rawpoly.png'), debug)
    cv2.imwrite(str(OUT_DIR / 'mask_rawpoly.png'), raw)
    cv2.imwrite(str(OUT_DIR / 'mask_softpoly.png'), soft)
    cv2.imwrite(str(OUT_DIR / 'erase_rawpoly_inpaint_hist.png'), out)
    grid = np.vstack([
        np.hstack([label(img,'original'), label(debug,'raw mediapipe polygon'), label(cv2.cvtColor(soft, cv2.COLOR_GRAY2BGR),'soft polygon mask')]),
        np.hstack([label(out,'rawpoly + inpaint + weak LAB'), label(out,'result'), label(out,'result')])
    ])
    cv2.imwrite(str(OUT_DIR / 'comparison_grid.png'), grid)
    print({'out_dir': str(OUT_DIR), 'boxes': boxes})

if __name__ == '__main__':
    main()
