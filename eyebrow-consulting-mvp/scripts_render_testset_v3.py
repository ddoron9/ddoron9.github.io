from pathlib import Path
import math
import cv2
import numpy as np

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
PROJECT = ROOT / 'eyebrow-consulting-mvp'
INPUTS = [PROJECT / 'web/sample.jpg']
OUT_DIR = ROOT / 'out/eyebrow_render_results_v3'
OUT_DIR.mkdir(parents=True, exist_ok=True)

STYLES = [
    dict(id='real_soft', name='실사 소프트', density=0.74, thickness=0.92, arch=0.10, tail=0.10, opacity=0.76, makeup=0.12),
    dict(id='real_balanced', name='실사 밸런스', density=0.86, thickness=1.02, arch=0.14, tail=0.14, opacity=0.83, makeup=0.20),
    dict(id='real_defined', name='실사 디파인드', density=0.95, thickness=1.10, arch=0.18, tail=0.18, opacity=0.88, makeup=0.28),
]

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
EYE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')


def detect_face(gray):
    faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(120, 120))
    if len(faces) == 0:
        h, w = gray.shape[:2]
        return int(w * 0.18), int(h * 0.12), int(w * 0.64), int(h * 0.78)
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return tuple(map(int, faces[0]))


def detect_eyes(gray, face):
    x, y, w, h = face
    roi = gray[y:y + int(h * 0.55), x:x + w]
    eyes = EYE_CASCADE.detectMultiScale(roi, scaleFactor=1.05, minNeighbors=6, minSize=(22, 12))
    candidates = []
    for ex, ey, ew, eh in eyes:
        cx = x + ex + ew / 2
        cy = y + ey + eh / 2
        if cy > y + h * 0.18 and cy < y + h * 0.52:
            candidates.append((cx, cy, ew, eh))
    candidates.sort(key=lambda e: e[0])
    if len(candidates) >= 2:
        left = candidates[0]
        right = candidates[-1]
        return left, right
    return (
        (x + w * 0.32, y + h * 0.40, w * 0.16, h * 0.07),
        (x + w * 0.68, y + h * 0.40, w * 0.16, h * 0.07),
    )


def percentile_or(gray, mask, q, fallback):
    vals = gray[mask > 0]
    return float(np.percentile(vals, q)) if vals.size else fallback


def detect_brow_polygon(img, gray, face, eye, side):
    x, y, w, h = face
    cx, cy, ew, eh = eye
    sx = int(max(x, cx - ew * 1.15))
    ex = int(min(x + w, cx + ew * 1.15))
    sy = int(max(y, cy - h * 0.18))
    ey = int(min(y + h * 0.42, cy - eh * 0.05))
    if ex - sx < 12 or ey - sy < 8:
        bw = w * 0.22
        bh = h * 0.05
        bx = cx - bw * (0.75 if side == 'left' else 0.25)
        by = cy - h * 0.14
        return box_polygon((bx, by, bw, bh), arch=0.12)

    patch = gray[sy:ey, sx:ex]
    blur = cv2.GaussianBlur(patch, (0, 0), 1.2)
    thr = np.percentile(blur, 22)
    dark = (blur < thr).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    dark = cv2.dilate(dark, np.ones((3, 5), np.uint8), iterations=1)

    labels, stats = cv2.connectedComponentsWithStats(dark, 8)[1:3]
    best = None
    best_score = -1
    for i in range(1, stats.shape[0]):
        x0, y0, ww, hh, area = stats[i]
        if area < 40:
            continue
        center_x = sx + x0 + ww / 2
        center_y = sy + y0 + hh / 2
        dist = abs(center_x - cx) / max(1, ew) + abs(center_y - (cy - eh * 0.9)) / max(1, eh)
        score = area - dist * 18
        if score > best_score:
            best_score = score
            best = (sx + x0, sy + y0, ww, hh)

    if best is None:
        bw = w * 0.22
        bh = h * 0.05
        bx = cx - bw * (0.75 if side == 'left' else 0.25)
        by = cy - h * 0.14
        return box_polygon((bx, by, bw, bh), arch=0.12)

    bx, by, bw, bh = best
    bx -= int(bw * 0.10)
    bw = int(bw * 1.20)
    by -= int(bh * 0.22)
    bh = int(bh * 1.35)
    bx = max(x, bx)
    by = max(y, by)
    bw = min(int(x + w - bx), bw)
    bh = min(int(y + h - by), bh)
    return box_polygon((bx, by, bw, bh), arch=0.16)


def box_polygon(box, arch=0.14):
    bx, by, bw, bh = map(float, box)
    ts = np.linspace(0, 1, 9)
    top = []
    bottom = []
    for t in ts:
        lift = math.exp(-((t - 0.48) / 0.24) ** 2) * bh * arch
        top.append([bx + bw * t, by + bh * (0.25 + 0.08 * abs(t - 0.5)) - lift])
        bottom.append([bx + bw * t, by + bh * (0.80 - 0.18 * (1 - abs(t - 0.5)))])
    poly = np.array(top + bottom[::-1], dtype=np.float32)
    return poly


def brow_mask(shape, poly, sigma=1.2, dilate=1):
    mask = np.zeros(shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(poly.astype(np.int32)), 255)
    if dilate:
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=dilate)
    if sigma > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), sigma)
    return mask


def sample_skin(img, face, brow_masks):
    x, y, w, h = face
    skin_mask = np.zeros(img.shape[:2], np.uint8)
    cv2.rectangle(skin_mask, (x, y), (x + w, y + h), 255, -1)
    for m in brow_masks:
        skin_mask[m > 0] = 0
    cheek = np.zeros_like(skin_mask)
    cv2.rectangle(cheek, (int(x + w * 0.18), int(y + h * 0.50)), (int(x + w * 0.82), int(y + h * 0.72)), 255, -1)
    forehead = np.zeros_like(skin_mask)
    cv2.rectangle(forehead, (int(x + w * 0.28), int(y + h * 0.14)), (int(x + w * 0.72), int(y + h * 0.25)), 255, -1)
    region = cv2.bitwise_or(cheek, forehead)
    region = cv2.bitwise_and(region, skin_mask)
    vals = img[region > 0]
    if vals.size == 0:
        vals = img[y:y + h, x:x + w].reshape(-1, 3)
    mean = vals.mean(axis=0)
    return mean.astype(np.float32)


def sample_hair_color(img, face):
    x, y, w, h = face
    sx = int(max(0, x + w * 0.20))
    sy = int(max(0, y - h * 0.12))
    ex = int(min(img.shape[1], x + w * 0.80))
    ey = int(min(img.shape[0], y + h * 0.08))
    patch = img[sy:ey, sx:ex]
    vals = patch.reshape(-1, 3)
    gray = vals @ np.array([0.114, 0.587, 0.299]) if vals.size else np.array([])
    sel = vals[gray < 135] if gray.size else np.empty((0, 3))
    if sel.size == 0:
        sel = vals if vals.size else np.array([[70, 60, 55]], dtype=np.float32)
    return sel.mean(axis=0).astype(np.float32)


def remove_brows(img, brow_masks, skin_color):
    merged = np.maximum.reduce(brow_masks)
    inpaint_mask = (merged > 18).astype(np.uint8) * 255
    base = cv2.inpaint(img, inpaint_mask, 3, cv2.INPAINT_TELEA)
    field = np.full_like(img, skin_color.astype(np.uint8))
    alpha = cv2.GaussianBlur(merged, (0, 0), 2.2).astype(np.float32) / 255.0
    alpha = np.clip(alpha * 0.88, 0, 0.88)[..., None]
    out = np.clip(base.astype(np.float32) * (1 - alpha) + field.astype(np.float32) * alpha, 0, 255).astype(np.uint8)
    out = cv2.bilateralFilter(out, 7, 18, 18)
    return out


def poly_centerline(poly, side):
    pts = poly[:, 0] if poly.ndim == 3 else poly
    top = pts[: len(pts) // 2]
    bottom = pts[len(pts) // 2 :][::-1]
    centers = (top + bottom) / 2
    thickness = np.linalg.norm(top - bottom, axis=1)
    if side == 'left':
        centers = centers[::-1]
        thickness = thickness[::-1]
    return centers.astype(np.float32), np.maximum(2.0, thickness.astype(np.float32))


def stylize_centers(centers, thickness, style):
    out = centers.copy()
    th = thickness.copy()
    span_y = max(2.0, float(np.ptp(centers[:, 1])))
    for i in range(len(out)):
        t = i / max(1, len(out) - 1)
        arch = math.exp(-((t - 0.52) / 0.22) ** 2)
        tail = max(0.0, (t - 0.58) / 0.42)
        out[i, 1] -= span_y * (style['arch'] * 0.26 * arch + style['tail'] * 0.08 * tail)
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


def strand_plan(poly, style, hair_color):
    pts = poly[:, 0] if poly.ndim == 3 else poly
    w = float(np.ptp(pts[:, 0]))
    h = float(np.ptp(pts[:, 1]))
    luma = hair_color @ np.array([0.114, 0.587, 0.299])
    darkness = 1.0 - luma / 255.0
    total = int(110 + w * 0.42 + h * 3.8 + style['density'] * 120 + darkness * 45)
    head = int(total * 0.24)
    body = int(total * 0.52)
    tail = total - head - body
    return dict(total=total, head=head, body=body, tail=tail)


def draw_brow(result, poly, style, hair_color, side):
    centers, thickness = poly_centerline(poly, side)
    centers, thickness = stylize_centers(centers, thickness, style)
    plan = strand_plan(poly, style, hair_color)
    clip = brow_mask(result.shape, poly, sigma=1.0, dilate=1).astype(np.float32) / 255.0
    layer = np.zeros_like(result)
    alpha = np.zeros(result.shape[:2], np.float32)

    body = np.array([max(6, hair_color[0] * 0.72), max(8, hair_color[1] * 0.72), max(10, hair_color[2] * 0.72)], dtype=np.float32)
    head = np.clip(body + np.array([18, 14, 10], dtype=np.float32), 0, 255)
    tail = np.clip(body - np.array([10, 10, 10], dtype=np.float32), 0, 255)

    rng = np.random.default_rng(abs(hash(style['id'] + side)) % (2 ** 32))

    shadow = np.zeros_like(result)
    cv2.fillConvexPoly(shadow, cv2.convexHull(poly.astype(np.int32)), tuple(map(int, body)))
    shadow = cv2.GaussianBlur(shadow, (0, 0), 1.2)
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


def render_case(src_path):
    img = cv2.imread(str(src_path))
    if img is None:
        raise RuntimeError(f'Failed to load {src_path}')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face = detect_face(gray)
    left_eye, right_eye = detect_eyes(gray, face)
    left_poly = detect_brow_polygon(img, gray, face, left_eye, 'left')
    right_poly = detect_brow_polygon(img, gray, face, right_eye, 'right')
    left_mask = brow_mask(img.shape, left_poly, sigma=1.2, dilate=1)
    right_mask = brow_mask(img.shape, right_poly, sigma=1.2, dilate=1)
    skin_color = sample_skin(img, face, [left_mask, right_mask])
    hair_color = sample_hair_color(img, face)
    clean = remove_brows(img, [left_mask, right_mask], skin_color)

    overlay = img.copy()
    cv2.rectangle(overlay, (face[0], face[1]), (face[0] + face[2], face[1] + face[3]), (0, 255, 255), 2)
    for eye, col in [(left_eye, (255, 200, 0)), (right_eye, (255, 200, 0))]:
        cx, cy, ew, eh = eye
        cv2.rectangle(overlay, (int(cx - ew / 2), int(cy - eh / 2)), (int(cx + ew / 2), int(cy + eh / 2)), col, 2)
    cv2.polylines(overlay, [left_poly.astype(np.int32)], True, (0, 0, 255), 2)
    cv2.polylines(overlay, [right_poly.astype(np.int32)], True, (255, 0, 0), 2)

    tiles = [panel_label(img, 'original'), panel_label(clean, 'cleaned'), panel_label(overlay, 'detected brows')]
    summaries = []
    for style in STYLES:
        res = clean.copy()
        res, left_plan = draw_brow(res, left_poly, style, hair_color, 'left')
        res, right_plan = draw_brow(res, right_poly, style, hair_color, 'right')
        count_text = f"{style['name']} | L {left_plan['total']} / R {right_plan['total']}"
        tiles.append(panel_label(res, count_text))
        cv2.imwrite(str(OUT_DIR / f"{src_path.stem}_{style['id']}.png"), res)
        summaries.append(dict(style=style['id'], left=left_plan, right=right_plan))

    grid = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:6])])
    cv2.imwrite(str(OUT_DIR / f'{src_path.stem}_grid.png'), grid)
    return dict(src=str(src_path), out=str(OUT_DIR / f'{src_path.stem}_grid.png'), summaries=summaries)


def main():
    reports = []
    for src in INPUTS:
        reports.append(render_case(src))
    for report in reports:
        print(report)


if __name__ == '__main__':
    main()
