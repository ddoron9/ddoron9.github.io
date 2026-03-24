from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
SRC = ROOT / 'eyebrow-consulting-mvp/web/sample.jpg'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
OUT_DIR = ROOT / 'out/eyebrow_blurfill_compare'
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


def pts(landmarks, idxs, w, h):
    return np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idxs], dtype=np.int32)


def masks(img, landmarks):
    h, w = img.shape[:2]
    conn = vision.FaceLandmarksConnections
    face_idx = sorted({i for c in conn.FACE_LANDMARKS_FACE_OVAL for i in (c.start, c.end)})
    brow_groups = [
        unique_indices(conn.FACE_LANDMARKS_LEFT_EYEBROW),
        unique_indices(conn.FACE_LANDMARKS_RIGHT_EYEBROW),
    ]
    eye_groups = [
        unique_indices(conn.FACE_LANDMARKS_LEFT_EYE),
        unique_indices(conn.FACE_LANDMARKS_RIGHT_EYE),
    ]
    lips_idx = unique_indices(conn.FACE_LANDMARKS_LIPS)

    face_mask = np.zeros((h, w), np.uint8)
    skin_mask = np.zeros((h, w), np.uint8)
    brow_raw = np.zeros((h, w), np.uint8)
    debug = img.copy()

    face_poly = cv2.convexHull(pts(landmarks, face_idx, w, h))
    cv2.fillConvexPoly(face_mask, face_poly, 255)
    cv2.polylines(debug, [face_poly], True, (255,255,255), 2)
    skin_mask[:] = face_mask

    for idxs, color in [(brow_groups[0], (0,0,255)), (brow_groups[1], (255,0,0))]:
        poly = cv2.convexHull(pts(landmarks, idxs, w, h))
        cv2.fillConvexPoly(brow_raw, poly, 255)
        cv2.polylines(debug, [poly], True, color, 2)
    for idxs in eye_groups + [lips_idx]:
        poly = cv2.convexHull(pts(landmarks, idxs, w, h))
        cv2.fillConvexPoly(skin_mask, poly, 0)
    skin_mask = cv2.subtract(skin_mask, brow_raw)

    # remove likely hair near forehead by darkness
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ys = face_poly[:,0,1]
    xs = face_poly[:,0,0]
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    forehead = np.zeros_like(skin_mask)
    cv2.rectangle(forehead, (x0, y0), (x1, y0 + max(8, int((y1-y0)*0.18))), 255, -1)
    dark = ((gray < np.percentile(gray[face_mask > 0], 30)) & (forehead > 0)).astype(np.uint8)*255
    skin_mask[dark > 0] = 0

    # skin heuristic
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    skin_like = ((Cr > 132) & (Cr < 180) & (Cb > 85) & (Cb < 140) & (Y > 60)).astype(np.uint8) * 255
    skin_mask = cv2.bitwise_and(skin_mask, skin_like)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))

    # feathered brow masks
    brow_soft = cv2.GaussianBlur(cv2.dilate(brow_raw, np.ones((3,3), np.uint8), iterations=1), (0,0), 1.2)
    brow_inner = cv2.GaussianBlur(brow_raw, (0,0), 0.8)
    return face_mask, skin_mask, brow_raw, brow_inner, brow_soft, debug


def skin_field(img, skin_mask, sigma):
    masked = img.copy().astype(np.float32)
    masked[skin_mask == 0] = 0
    weight = cv2.GaussianBlur((skin_mask/255.0).astype(np.float32), (0,0), sigma)
    out = np.zeros_like(masked)
    for c in range(3):
        blur = cv2.GaussianBlur(masked[...,c], (0,0), sigma)
        out[...,c] = blur / np.maximum(weight, 1e-4)
    return np.clip(out, 0, 255).astype(np.uint8)


def inpaint_base(img, brow_soft):
    return cv2.inpaint(img, (brow_soft > 20).astype(np.uint8)*255, 2, cv2.INPAINT_TELEA)


def blend_fill(base, field, inner_alpha, edge_alpha, inner_w=0.7, edge_w=0.35, bilateral=False):
    a_in = (inner_alpha.astype(np.float32)/255.0) * inner_w
    a_ed = (edge_alpha.astype(np.float32)/255.0) * edge_w
    a = np.clip(np.maximum(a_in, a_ed), 0, 0.92)[...,None]
    out = np.clip(base.astype(np.float32)*(1-a) + field.astype(np.float32)*a, 0, 255).astype(np.uint8)
    if bilateral:
        out = cv2.bilateralFilter(out, 5, 18, 18)
    return out


def weak_tone_align(img, skin_mask, brow_soft):
    out = img.copy().astype(np.float32)
    alpha = (brow_soft.astype(np.float32)/255.0)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    skin_vals = lab[skin_mask > 0]
    skin_mean = skin_vals.mean(axis=0)
    active = alpha > 0.08
    roi_mean = lab[active].mean(axis=0) if np.any(active) else skin_mean
    shift = skin_mean - roi_mean
    lab[...,0] += alpha * shift[0] * 0.18
    lab[...,1] += alpha * shift[1] * 0.28
    lab[...,2] += alpha * shift[2] * 0.28
    out = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return out


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0,0), (out.shape[1], 42), (20,20,20), -1)
    cv2.putText(out, text, (12, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
    return out


def main():
    img = cv2.imread(str(SRC))
    landmarks = load_landmarks()
    face_mask, skin_mask, brow_raw, brow_inner, brow_soft, debug = masks(img, landmarks)
    base = inpaint_base(img, brow_soft)
    field_soft = skin_field(img, skin_mask, sigma=13)
    field_strong = skin_field(img, skin_mask, sigma=21)

    a = blend_fill(base, field_soft, brow_inner, brow_soft, inner_w=0.55, edge_w=0.22, bilateral=False)
    b = blend_fill(base, field_strong, brow_inner, brow_soft, inner_w=0.72, edge_w=0.30, bilateral=True)
    c0 = blend_fill(base, field_strong, brow_inner, brow_soft, inner_w=0.65, edge_w=0.26, bilateral=True)
    c = weak_tone_align(c0, skin_mask, brow_soft)

    cv2.imwrite(str(OUT_DIR / 'debug_overlay.png'), debug)
    cv2.imwrite(str(OUT_DIR / 'mask_skin_only.png'), skin_mask)
    cv2.imwrite(str(OUT_DIR / 'mask_brow_raw.png'), brow_raw)
    cv2.imwrite(str(OUT_DIR / 'mask_brow_soft.png'), brow_soft)
    cv2.imwrite(str(OUT_DIR / 'erase_blurfill_soft.png'), a)
    cv2.imwrite(str(OUT_DIR / 'erase_blurfill_strong.png'), b)
    cv2.imwrite(str(OUT_DIR / 'erase_blurfill_tonealign.png'), c)

    grid = np.vstack([
        np.hstack([
            label(img, 'original'),
            label(debug, 'overlay'),
            label(cv2.cvtColor(brow_soft, cv2.COLOR_GRAY2BGR), 'soft brow mask')
        ]),
        np.hstack([
            label(a, 'A blur-fill soft'),
            label(b, 'B blur-fill stronger'),
            label(c, 'C blur-fill + weak tone align')
        ])
    ])
    cv2.imwrite(str(OUT_DIR / 'comparison_grid.png'), grid)
    print({'out_dir': str(OUT_DIR), 'skin_pixels': int((skin_mask > 0).sum())})

if __name__ == '__main__':
    main()
