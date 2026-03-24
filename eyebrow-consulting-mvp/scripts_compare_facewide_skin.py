from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
SRC = ROOT / 'eyebrow-consulting-mvp/web/sample.jpg'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
OUT_DIR = ROOT / 'out/eyebrow_facewide_compare'
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


def build_face_and_feature_masks(img, landmarks):
    h, w = img.shape[:2]
    conn = vision.FaceLandmarksConnections

    face_idx = sorted({i for c in conn.FACE_LANDMARKS_FACE_OVAL for i in (c.start, c.end)})
    left_brow_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYEBROW)
    right_brow_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYEBROW)
    left_eye_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYE)
    right_eye_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYE)
    lips_idx = unique_indices(conn.FACE_LANDMARKS_LIPS)

    face_mask = np.zeros((h, w), np.uint8)
    exclude_mask = np.zeros((h, w), np.uint8)
    brow_mask = np.zeros((h, w), np.uint8)
    debug = img.copy()

    face_poly = cv2.convexHull(pts(landmarks, face_idx, w, h))
    cv2.fillConvexPoly(face_mask, face_poly, 255)
    cv2.polylines(debug, [face_poly], True, (255,255,255), 2)

    for idxs, color, target in [
        (left_brow_idx, (0,0,255), brow_mask),
        (right_brow_idx, (255,0,0), brow_mask),
        (left_eye_idx, (0,255,255), exclude_mask),
        (right_eye_idx, (0,255,255), exclude_mask),
        (lips_idx, (255,0,255), exclude_mask),
    ]:
        poly = cv2.convexHull(pts(landmarks, idxs, w, h))
        cv2.fillConvexPoly(target, poly, 255)
        cv2.polylines(debug, [poly], True, color, 2)

    # add brows into exclude too
    exclude_mask = cv2.max(exclude_mask, brow_mask)

    # conservative hair suppression: upper face band + dark pixels near forehead/hairline
    ys = [p[1] for p in face_poly[:,0,:]]
    xs = [p[0] for p in face_poly[:,0,:]]
    x0, x1 = max(0, min(xs)), min(w, max(xs))
    y0, y1 = max(0, min(ys)), min(h, max(ys))
    forehead_band = np.zeros_like(face_mask)
    fb_h = max(8, int((y1-y0) * 0.18))
    cv2.rectangle(forehead_band, (x0, y0), (x1, y0 + fb_h), 255, -1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dark_hair = ((gray < np.percentile(gray[face_mask > 0], 28)) & (forehead_band > 0)).astype(np.uint8) * 255
    dark_hair = cv2.dilate(dark_hair, np.ones((5,5), np.uint8), iterations=1)
    exclude_mask = cv2.max(exclude_mask, dark_hair)

    skin_mask = cv2.subtract(face_mask, exclude_mask)

    # refine skin candidates with YCrCb heuristic
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    skin_like = ((Cr > 132) & (Cr < 180) & (Cb > 85) & (Cb < 140) & (Y > 60)).astype(np.uint8) * 255
    skin_mask = cv2.bitwise_and(skin_mask, skin_like)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))

    soft_brow = cv2.GaussianBlur(cv2.dilate(brow_mask, np.ones((3,3), np.uint8), iterations=1), (0,0), 1.2)
    return face_mask, skin_mask, brow_mask, soft_brow, debug


def robust_lab_stats(img, mask):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    vals = lab[mask > 0]
    if len(vals) < 10:
        vals = lab.reshape(-1, 3)
    mean = vals.mean(axis=0)
    std = vals.std(axis=0) + 1e-6
    return mean, std, lab


def build_skin_field(img, skin_mask):
    masked = img.copy()
    masked[skin_mask == 0] = 0
    weight = cv2.GaussianBlur((skin_mask / 255.0).astype(np.float32), (0,0), 21)
    field = np.zeros_like(img, dtype=np.float32)
    for c in range(3):
        blur = cv2.GaussianBlur(masked[..., c].astype(np.float32), (0,0), 21)
        field[..., c] = blur / np.maximum(weight, 1e-4)
    field = np.clip(field, 0, 255).astype(np.uint8)
    return field


def histogram_match_channel(src, ref):
    src = np.clip(src, 0, 255).astype(np.uint8)
    ref = np.clip(ref, 0, 255).astype(np.uint8)
    s_hist, _ = np.histogram(src.flatten(), 256, [0,256], density=True)
    r_hist, _ = np.histogram(ref.flatten(), 256, [0,256], density=True)
    s_cdf = np.cumsum(s_hist)
    r_cdf = np.cumsum(r_hist)
    lut = np.interp(s_cdf, r_cdf, np.arange(256))
    return lut[src].astype(np.uint8)


def inpaint_base(img, soft_brow):
    return cv2.inpaint(img, (soft_brow > 20).astype(np.uint8) * 255, 2, cv2.INPAINT_TELEA)


def algo_lab_global(img, soft_brow, skin_mask):
    base = inpaint_base(img, soft_brow)
    alpha = (soft_brow.astype(np.float32) / 255.0)
    skin_mean, skin_std, _ = robust_lab_stats(img, skin_mask)
    lab = cv2.cvtColor(base, cv2.COLOR_BGR2LAB).astype(np.float32)
    active = alpha > 0.08
    roi = lab[active]
    if len(roi) > 0:
        roi_mean = roi.mean(axis=0)
        roi_std = roi.std(axis=0) + 1e-6
        lab2 = lab.copy()
        for c, strength in zip(range(3), [0.35, 0.7, 0.7]):
            shifted = ((lab[..., c] - roi_mean[c]) * (skin_std[c] / roi_std[c]) + skin_mean[c])
            lab2[..., c] = lab[..., c] * (1 - alpha * strength) + shifted * (alpha * strength)
        lab = np.clip(lab2, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def algo_hist_field(img, soft_brow, skin_mask):
    base = inpaint_base(img, soft_brow)
    alpha = (soft_brow.astype(np.float32) / 255.0)
    field = build_skin_field(img, skin_mask)
    skin_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    base_lab = cv2.cvtColor(base, cv2.COLOR_BGR2LAB)
    ref_L = skin_lab[...,0][skin_mask > 0]
    out_lab = base_lab.copy()
    active = alpha > 0.08
    if np.any(active) and len(ref_L) > 10:
        matched = histogram_match_channel(base_lab[...,0][active], ref_L)
        out_lab[...,0][active] = (base_lab[...,0][active].astype(np.float32) * 0.45 + matched.astype(np.float32) * 0.55).astype(np.uint8)
    out = cv2.cvtColor(out_lab, cv2.COLOR_LAB2BGR)
    out = np.clip(out.astype(np.float32) * (1 - alpha[...,None] * 0.35) + field.astype(np.float32) * (alpha[...,None] * 0.35), 0, 255).astype(np.uint8)
    return out


def algo_shadow_suppress(img, soft_brow, skin_mask):
    out = algo_hist_field(img, soft_brow, skin_mask)
    alpha = (soft_brow.astype(np.float32) / 255.0)
    gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ref_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[skin_mask > 0].astype(np.float32)
    target = np.percentile(ref_gray, 35) if len(ref_gray) > 10 else gray.mean()
    residual = np.clip((target - gray) / 40.0, 0, 1) * alpha
    lift = (10 + 18 * residual)[...,None]
    warm = np.dstack([lift * 0.92, lift * 0.72, lift * 0.62])
    out2 = np.clip(out.astype(np.float32) + warm * residual[...,None] * 0.35, 0, 255).astype(np.uint8)
    out2 = cv2.bilateralFilter(out2, 5, 20, 20)
    return out2


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0,0), (out.shape[1], 42), (20,20,20), -1)
    cv2.putText(out, text, (12, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
    return out


def main():
    img = cv2.imread(str(SRC))
    landmarks = load_landmarks()
    face_mask, skin_mask, brow_mask, soft_brow, debug = build_face_and_feature_masks(img, landmarks)

    a = algo_lab_global(img, soft_brow, skin_mask)
    b = algo_hist_field(img, soft_brow, skin_mask)
    c = algo_shadow_suppress(img, soft_brow, skin_mask)

    cv2.imwrite(str(OUT_DIR / 'debug_face_features.png'), debug)
    cv2.imwrite(str(OUT_DIR / 'mask_face.png'), face_mask)
    cv2.imwrite(str(OUT_DIR / 'mask_skin_only.png'), skin_mask)
    cv2.imwrite(str(OUT_DIR / 'mask_brow_soft.png'), soft_brow)
    cv2.imwrite(str(OUT_DIR / 'erase_lab_global.png'), a)
    cv2.imwrite(str(OUT_DIR / 'erase_hist_field.png'), b)
    cv2.imwrite(str(OUT_DIR / 'erase_shadow_suppress.png'), c)

    grid = np.vstack([
        np.hstack([
            label(img, 'original'),
            label(debug, 'face/features overlay'),
            label(cv2.cvtColor(skin_mask, cv2.COLOR_GRAY2BGR), 'skin-only mask')
        ]),
        np.hstack([
            label(a, 'A global LAB match'),
            label(b, 'B L-hist + skin blur field'),
            label(c, 'C B + dark shadow suppression')
        ])
    ])
    cv2.imwrite(str(OUT_DIR / 'comparison_grid.png'), grid)
    print({'out_dir': str(OUT_DIR), 'skin_pixels': int((skin_mask > 0).sum()), 'brow_pixels': int((soft_brow > 20).sum())})

if __name__ == '__main__':
    main()
