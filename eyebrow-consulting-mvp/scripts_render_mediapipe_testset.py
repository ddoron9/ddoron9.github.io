from pathlib import Path
import math
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
PROJECT = ROOT / 'eyebrow-consulting-mvp'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
INPUTS = [PROJECT / 'web/sample.jpg']
OUT_DIR = ROOT / 'out/eyebrow_render_results_mp'
OUT_DIR.mkdir(parents=True, exist_ok=True)

STYLES = [
    dict(id='real_soft', name='실사 소프트', density=0.74, thickness=0.92, arch=0.10, tail=0.10, opacity=0.76),
    dict(id='real_balanced', name='실사 밸런스', density=0.86, thickness=1.02, arch=0.14, tail=0.14, opacity=0.83),
    dict(id='real_defined', name='실사 디파인드', density=0.95, thickness=1.10, arch=0.18, tail=0.18, opacity=0.88),
]


def create_landmarker():
    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL)),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    return vision.FaceLandmarker.create_from_options(options)


def unique_indices(edges):
    return sorted({c.start for c in edges} | {c.end for c in edges})


def points_from_landmarks(landmarks, idxs, w, h):
    return np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idxs], dtype=np.float32)


def hull_mask(shape, pts, sigma=0.0, dilate=0):
    hull = cv2.convexHull(pts.astype(np.int32))[:, 0, :].astype(np.float32)
    mask = np.zeros(shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, hull.astype(np.int32), 255)
    if dilate:
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=dilate)
    if sigma > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), sigma)
    return hull, mask


def extract_geometry(img, landmarks):
    h, w = img.shape[:2]
    conn = vision.FaceLandmarksConnections
    face_idx = sorted({i for c in conn.FACE_LANDMARKS_FACE_OVAL for i in (c.start, c.end)})
    left_brow_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYEBROW)
    right_brow_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYEBROW)
    left_eye_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYE)
    right_eye_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYE)
    lips_idx = unique_indices(conn.FACE_LANDMARKS_LIPS)

    face_pts = points_from_landmarks(landmarks, face_idx, w, h)
    left_brow_pts = points_from_landmarks(landmarks, left_brow_idx, w, h)
    right_brow_pts = points_from_landmarks(landmarks, right_brow_idx, w, h)
    left_eye_pts = points_from_landmarks(landmarks, left_eye_idx, w, h)
    right_eye_pts = points_from_landmarks(landmarks, right_eye_idx, w, h)
    lips_pts = points_from_landmarks(landmarks, lips_idx, w, h)

    face_hull, face_mask = hull_mask(img.shape, face_pts)
    left_brow_hull, left_brow_mask = hull_mask(img.shape, left_brow_pts, sigma=0.8, dilate=1)
    right_brow_hull, right_brow_mask = hull_mask(img.shape, right_brow_pts, sigma=0.8, dilate=1)
    left_eye_hull, _ = hull_mask(img.shape, left_eye_pts)
    right_eye_hull, _ = hull_mask(img.shape, right_eye_pts)
    lips_hull, _ = hull_mask(img.shape, lips_pts)

    skin_mask = face_mask.copy()
    for poly in [left_brow_hull, right_brow_hull, left_eye_hull, right_eye_hull, lips_hull]:
        cv2.fillConvexPoly(skin_mask, poly.astype(np.int32), 0)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    merged_brow = np.maximum(left_brow_mask, right_brow_mask)
    return dict(
        face_hull=face_hull,
        face_mask=face_mask,
        left_brow_hull=left_brow_hull,
        right_brow_hull=right_brow_hull,
        left_eye_hull=left_eye_hull,
        right_eye_hull=right_eye_hull,
        lips_hull=lips_hull,
        skin_mask=skin_mask,
        brow_mask=merged_brow,
    )


def sample_skin(img, skin_mask):
    vals = img[skin_mask > 0]
    if vals.size == 0:
        vals = img.reshape(-1, 3)
    return vals.mean(axis=0).astype(np.float32)


def sample_hair_color(img, face_hull):
    x0, y0 = np.min(face_hull[:, 0]), np.min(face_hull[:, 1])
    x1, y1 = np.max(face_hull[:, 0]), np.max(face_hull[:, 1])
    sx = int(max(0, x0 + (x1 - x0) * 0.2))
    ex = int(min(img.shape[1], x0 + (x1 - x0) * 0.8))
    sy = int(max(0, y0 - (y1 - y0) * 0.14))
    ey = int(min(img.shape[0], y0 + (y1 - y0) * 0.08))
    patch = img[sy:ey, sx:ex]
    vals = patch.reshape(-1, 3)
    gray = vals @ np.array([0.114, 0.587, 0.299]) if vals.size else np.array([])
    sel = vals[gray < 135] if gray.size else np.empty((0, 3))
    if sel.size == 0:
        sel = vals if vals.size else np.array([[70, 60, 55]], dtype=np.float32)
    return sel.mean(axis=0).astype(np.float32)


def remove_brows(img, brow_mask, skin_color):
    inpaint_mask = (brow_mask > 20).astype(np.uint8) * 255
    base = cv2.inpaint(img, inpaint_mask, 3, cv2.INPAINT_TELEA)
    field = np.full_like(img, skin_color.astype(np.uint8))
    alpha = cv2.GaussianBlur(brow_mask, (0, 0), 2.0).astype(np.float32) / 255.0
    alpha = np.clip(alpha * 0.85, 0, 0.85)[..., None]
    out = np.clip(base.astype(np.float32) * (1 - alpha) + field.astype(np.float32) * alpha, 0, 255).astype(np.uint8)
    return cv2.bilateralFilter(out, 7, 18, 18)


def centerline_from_hull(hull, side):
    pts = hull[np.argsort(hull[:, 0])]
    if side == 'left':
        pts = pts[::-1]
    buckets = np.array_split(pts, min(7, len(pts)))
    centers = []
    thickness = []
    for b in buckets:
        centers.append([float(np.mean(b[:, 0])), float((np.min(b[:, 1]) + np.max(b[:, 1])) / 2)])
        thickness.append(max(2.0, float(np.max(b[:, 1]) - np.min(b[:, 1]) + 1.0)))
    return np.array(centers, dtype=np.float32), np.array(thickness, dtype=np.float32)


def stylize_centers(centers, thickness, style):
    out = centers.copy()
    th = thickness.copy()
    span_y = max(2.0, float(np.ptp(centers[:, 1])))
    for i in range(len(out)):
        t = i / max(1, len(out) - 1)
        arch = math.exp(-((t - 0.52) / 0.22) ** 2)
        tail = max(0.0, (t - 0.58) / 0.42)
        out[i, 1] -= span_y * (style['arch'] * 0.28 * arch + style['tail'] * 0.09 * tail)
        fullness = 0.72 + (1 - abs(t - 0.46) * 1.25) * 0.24
        taper = 1 - max(0.0, t - 0.74) * 0.56
        th[i] *= max(0.55, style['thickness'] * fullness * taper)
    return out, th


def sample_curve(curve, t):
    if len(curve) == 1:
        return curve[0]
    x = t * (len(curve) - 1)
    i = min(len(curve) - 2, int(x))
    a = x - i
    return curve[i] * (1 - a) + curve[i + 1] * a


def tangent(curve, t):
    p0 = sample_curve(curve, max(0, t - 0.03))
    p1 = sample_curve(curve, min(1, t + 0.03))
    v = p1 - p0
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else np.array([1.0, 0.0], dtype=np.float32)


def alpha_blend(base, layer, alpha):
    a = np.clip(alpha[..., None], 0, 1)
    return np.clip(base.astype(np.float32) * (1 - a) + layer.astype(np.float32) * a, 0, 255).astype(np.uint8)


def strand_plan(hull, style, hair_color):
    w = float(np.ptp(hull[:, 0]))
    h = float(np.ptp(hull[:, 1]))
    luma = hair_color @ np.array([0.114, 0.587, 0.299])
    darkness = 1.0 - luma / 255.0
    total = int(95 + w * 0.36 + h * 3.4 + style['density'] * 110 + darkness * 40)
    head = int(total * 0.24)
    body = int(total * 0.52)
    tail = total - head - body
    return dict(total=total, head=head, body=body, tail=tail)


def draw_brow(result, hull, style, hair_color, side):
    centers, thickness = centerline_from_hull(hull, side)
    centers, thickness = stylize_centers(centers, thickness, style)
    plan = strand_plan(hull, style, hair_color)
    clip = np.zeros(result.shape[:2], np.uint8)
    cv2.fillConvexPoly(clip, cv2.convexHull(hull.astype(np.int32)), 255)
    clip = cv2.GaussianBlur(cv2.dilate(clip, np.ones((3, 3), np.uint8), iterations=1), (0, 0), 0.8).astype(np.float32) / 255.0
    layer = np.zeros_like(result)
    alpha = np.zeros(result.shape[:2], np.float32)

    body = np.array([max(6, hair_color[0] * 0.72), max(8, hair_color[1] * 0.72), max(10, hair_color[2] * 0.72)], dtype=np.float32)
    head = np.clip(body + np.array([18, 14, 10], dtype=np.float32), 0, 255)
    tail = np.clip(body - np.array([10, 10, 10], dtype=np.float32), 0, 255)
    rng = np.random.default_rng(abs(hash(style['id'] + side)) % (2 ** 32))

    shadow = np.zeros_like(result)
    cv2.fillConvexPoly(shadow, cv2.convexHull(hull.astype(np.int32)), tuple(map(int, body)))
    shadow = cv2.GaussianBlur(shadow, (0, 0), 1.1)
    layer = alpha_blend(layer, shadow, clip * (0.05 + style['opacity'] * 0.04))
    alpha = np.maximum(alpha, clip * 0.05)

    def emit(zone, count, t0, t1, color, bias, alpha_base, len_scale):
        nonlocal layer, alpha
        for i in range(count):
            t = t0 + (t1 - t0) * ((i + rng.random() * 0.2) / max(1, count - 1))
            c = sample_curve(centers, t)
            tan = tangent(centers, t)
            ang = math.atan2(float(tan[1]), float(tan[0])) + bias + rng.normal(0, 0.08 if zone == 'body' else 0.11)
            idx = min(len(thickness) - 1, int(round(t * (len(thickness) - 1))))
            offset = rng.uniform(-0.24, 0.24) * thickness[idx]
            root = np.array([c[0] + math.sin(ang + math.pi / 2) * offset, c[1] - math.cos(ang + math.pi / 2) * offset], dtype=np.float32)
            length = thickness[idx] * len_scale * rng.uniform(0.78, 1.16)
            tip = root + np.array([math.cos(ang) * length, math.sin(ang) * length], dtype=np.float32)
            ctrl = root + (tip - root) * 0.46 + np.array([math.cos(ang - 0.9), math.sin(ang - 0.9)], dtype=np.float32) * length * 0.08
            width = max(1, int((1.0 if zone == 'body' else 0.8) * rng.uniform(0.8, 1.2) * style['thickness']))
            temp = np.zeros_like(result)
            cv2.line(temp, tuple(root.astype(int)), tuple(ctrl.astype(int)), tuple(map(int, color)), width, cv2.LINE_AA)
            cv2.line(temp, tuple(ctrl.astype(int)), tuple(tip.astype(int)), tuple(map(int, color)), max(1, width - 1), cv2.LINE_AA)
            mask = cv2.cvtColor(temp, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
            mask *= clip * alpha_base
            layer = alpha_blend(layer, temp, mask)
            alpha = np.maximum(alpha, mask * 0.9)

    emit('head', plan['head'], 0.00, 0.24, head, -0.70, 0.18 * style['opacity'], 1.55)
    emit('body', plan['body'], 0.18, 0.82, body, -0.08, 0.30 * style['opacity'], 1.90)
    emit('tail', plan['tail'], 0.76, 1.00, tail, 0.10, 0.22 * style['opacity'], 1.25)
    result = alpha_blend(result, layer, alpha)
    return result, plan


def panel_label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 46), (22, 22, 22), -1)
    cv2.putText(out, text, (14, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def render_case(landmarker, src_path):
    img = cv2.imread(str(src_path))
    mp_img = mp.Image.create_from_file(str(src_path))
    det = landmarker.detect(mp_img)
    if not det.face_landmarks:
        raise RuntimeError(f'No face landmarks for {src_path}')
    geom = extract_geometry(img, det.face_landmarks[0])
    skin = sample_skin(img, geom['skin_mask'])
    hair = sample_hair_color(img, geom['face_hull'])
    clean = remove_brows(img, geom['brow_mask'], skin)

    overlay = img.copy()
    cv2.polylines(overlay, [geom['face_hull'].astype(np.int32)], True, (0, 255, 255), 1)
    cv2.polylines(overlay, [geom['left_eye_hull'].astype(np.int32)], True, (0, 200, 255), 1)
    cv2.polylines(overlay, [geom['right_eye_hull'].astype(np.int32)], True, (0, 200, 255), 1)
    cv2.polylines(overlay, [geom['left_brow_hull'].astype(np.int32)], True, (0, 0, 255), 2)
    cv2.polylines(overlay, [geom['right_brow_hull'].astype(np.int32)], True, (255, 0, 0), 2)

    tiles = [panel_label(img, 'original'), panel_label(clean, 'cleaned'), panel_label(overlay, 'mediapipe brows')]
    summaries = []
    for style in STYLES:
        res = clean.copy()
        res, left_plan = draw_brow(res, geom['left_brow_hull'], style, hair, 'left')
        res, right_plan = draw_brow(res, geom['right_brow_hull'], style, hair, 'right')
        tiles.append(panel_label(res, f"{style['name']} | L {left_plan['total']} / R {right_plan['total']}"))
        cv2.imwrite(str(OUT_DIR / f"{src_path.stem}_{style['id']}.png"), res)
        summaries.append(dict(style=style['id'], left=left_plan, right=right_plan))

    grid = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:6])])
    cv2.imwrite(str(OUT_DIR / f'{src_path.stem}_grid.png'), grid)
    return dict(src=str(src_path), out=str(OUT_DIR / f'{src_path.stem}_grid.png'), summaries=summaries)


def main():
    landmarker = create_landmarker()
    reports = []
    for src in INPUTS:
        reports.append(render_case(landmarker, src))
    for report in reports:
        print(report)


if __name__ == '__main__':
    main()
