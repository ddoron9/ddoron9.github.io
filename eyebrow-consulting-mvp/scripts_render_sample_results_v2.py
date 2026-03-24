from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
SRC = ROOT / 'eyebrow-consulting-mvp/web/sample.jpg'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
OUT_DIR = ROOT / 'out/eyebrow_render_results_v2'
OUT_DIR.mkdir(parents=True, exist_ok=True)

STYLES = [
    dict(id='natural_soft_arch', name='내추럴 소프트 아치', shape='soft', density=0.78, thickness=0.9, arch=0.10, tail=0.10, opacity=0.78),
    dict(id='defined_arch_taper', name='디파인드 테이퍼 아치', shape='high', density=0.88, thickness=1.0, arch=0.18, tail=0.18, opacity=0.84),
    dict(id='balanced_soft_full', name='밸런스드 소프트 풀브로우', shape='soft', density=0.92, thickness=1.08, arch=0.12, tail=0.14, opacity=0.88),
]


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
    return np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idxs], dtype=np.float32)


def convex_mask(shape, pts_arr, blur=0):
    mask = np.zeros(shape[:2], np.uint8)
    hull = cv2.convexHull(pts_arr.astype(np.int32))
    cv2.fillConvexPoly(mask, hull, 255)
    if blur > 0:
        mask = cv2.GaussianBlur(mask, (0,0), blur)
    return mask, hull[:,0,:].astype(np.float32)


def build_masks(img, landmarks):
    h, w = img.shape[:2]
    conn = vision.FaceLandmarksConnections
    face_idx = sorted({i for c in conn.FACE_LANDMARKS_FACE_OVAL for i in (c.start, c.end)})
    left_idx = unique_indices(conn.FACE_LANDMARKS_LEFT_EYEBROW)
    right_idx = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYEBROW)
    left_eye = unique_indices(conn.FACE_LANDMARKS_LEFT_EYE)
    right_eye = unique_indices(conn.FACE_LANDMARKS_RIGHT_EYE)
    lips_idx = unique_indices(conn.FACE_LANDMARKS_LIPS)

    face_mask, face_hull = convex_mask(img.shape, pts(landmarks, face_idx, w, h))
    left_mask, left_hull = convex_mask(img.shape, pts(landmarks, left_idx, w, h))
    right_mask, right_hull = convex_mask(img.shape, pts(landmarks, right_idx, w, h))
    brow_raw = cv2.max(left_mask, right_mask)
    brow_soft = cv2.GaussianBlur(cv2.dilate(brow_raw, np.ones((3,3), np.uint8), iterations=1), (0,0), 1.2)
    brow_inner = cv2.GaussianBlur(brow_raw, (0,0), 0.8)

    skin_mask = face_mask.copy()
    for idxs in [left_eye, right_eye, lips_idx, left_idx, right_idx]:
        poly = cv2.convexHull(pts(landmarks, idxs, w, h).astype(np.int32))
        cv2.fillConvexPoly(skin_mask, poly, 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ys = face_hull[:,1]; xs = face_hull[:,0]
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    forehead = np.zeros_like(skin_mask)
    cv2.rectangle(forehead, (x0,y0), (x1, y0 + max(8, int((y1-y0)*0.18))), 255, -1)
    dark = ((gray < np.percentile(gray[face_mask > 0], 30)) & (forehead > 0)).astype(np.uint8)*255
    skin_mask[dark > 0] = 0
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    skin_like = ((Cr > 132) & (Cr < 180) & (Cb > 85) & (Cb < 140) & (Y > 60)).astype(np.uint8) * 255
    skin_mask = cv2.bitwise_and(skin_mask, skin_like)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    return skin_mask, brow_inner, brow_soft, left_hull, right_hull, face_hull


def skin_field(img, skin_mask, sigma=21):
    masked = img.astype(np.float32).copy(); masked[skin_mask == 0] = 0
    weight = cv2.GaussianBlur((skin_mask/255.0).astype(np.float32), (0,0), sigma)
    out = np.zeros_like(masked)
    for c in range(3):
        blur = cv2.GaussianBlur(masked[...,c], (0,0), sigma)
        out[...,c] = blur / np.maximum(weight, 1e-4)
    return np.clip(out, 0, 255).astype(np.uint8)


def c3_remove(img, skin_mask, brow_inner, brow_soft):
    base = cv2.inpaint(img, (brow_soft > 20).astype(np.uint8)*255, 2, cv2.INPAINT_TELEA)
    field = skin_field(img, skin_mask, 21)
    a_in = (brow_inner.astype(np.float32)/255.0) * 0.65
    a_ed = (brow_soft.astype(np.float32)/255.0) * 0.26
    a = np.clip(np.maximum(a_in, a_ed), 0, 0.9)[...,None]
    out = np.clip(base.astype(np.float32)*(1-a) + field.astype(np.float32)*a, 0, 255).astype(np.uint8)
    alpha = (brow_soft.astype(np.float32)/255.0)
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB).astype(np.float32)
    skin_lab = cv2.cvtColor(field, cv2.COLOR_BGR2LAB).astype(np.float32)
    active = alpha > 0.08
    if np.any(active):
        roi_mean = np.array([lab[...,c][active].mean() for c in range(3)])
        skin_mean = np.array([skin_lab[...,c][skin_mask > 0].mean() for c in range(3)])
        shift = skin_mean - roi_mean
        lab[...,0] += alpha * shift[0] * 0.08
        lab[...,1] += alpha * shift[1] * 0.22
        lab[...,2] += alpha * shift[2] * 0.22
    out = cv2.cvtColor(np.clip(lab,0,255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return out


def sample_hair_color(img, face_hull):
    x0, y0 = np.min(face_hull[:,0]), np.min(face_hull[:,1])
    x1, y1 = np.max(face_hull[:,0]), np.max(face_hull[:,1])
    sx = int(max(0, x0 + 0.2*(x1-x0)))
    sy = int(max(0, y0 - 0.14*(y1-y0)))
    sw = int(min(img.shape[1]-sx, 0.6*(x1-x0)))
    sh = int(min(img.shape[0]-sy, 0.16*(y1-y0)))
    patch = img[max(0,sy):max(0,sy)+max(2,sh), max(0,sx):max(0,sx)+max(2,sw)]
    vals = patch.reshape(-1,3)
    gray = vals @ np.array([0.114,0.587,0.299])
    sel = vals[gray < 130]
    if len(sel) < 8: sel = vals
    return sel.mean(axis=0)


def hull_curve(hull, side):
    order = np.argsort(hull[:,0])
    pts = hull[order]
    if side == 'left': pts = pts[::-1]
    buckets = np.array_split(pts, min(7, len(pts)))
    centers = []
    thickness = []
    for b in buckets:
        centers.append([float(np.mean(b[:,0])), float((np.min(b[:,1])+np.max(b[:,1]))/2)])
        thickness.append(max(2.0, float(np.max(b[:,1]) - np.min(b[:,1]) + 1.0)))
    return np.array(centers, dtype=np.float32), np.array(thickness, dtype=np.float32)


def stylize_curve(centers, thickness, style):
    out = centers.copy(); th = thickness.copy(); y_span = max(2.0, float(np.ptp(centers[:,1])))
    for i in range(len(centers)):
        t = i / max(1, len(centers)-1)
        arch = np.exp(-((t-0.52)/0.22)**2)
        front = max(0, 1-t/0.26)
        tail = max(0, (t-0.56)/0.44)
        out[i,1] += y_span*0.08 - y_span*(style['arch']*0.22*arch - 0.02*front + style['tail']*0.08*tail)
        th[i] *= (0.9 + 0.35*style['thickness']) * (0.7 + (1-abs(t-0.46)*1.3)*0.22) * (0.75 + min(1,t*3)*0.16) * (1-max(0,t-0.74)*0.52)
    return out, np.maximum(2.2, th)


def sample_curve(curve, t):
    x = t * (len(curve)-1)
    i = min(len(curve)-2, int(x)) if len(curve) > 1 else 0
    a = x - i if len(curve) > 1 else 0
    return curve[i]*(1-a) + curve[min(i+1, len(curve)-1)]*a


def tangent(curve, t):
    p0 = sample_curve(curve, max(0, t-0.03))
    p1 = sample_curve(curve, min(1, t+0.03))
    v = p1-p0; n = np.linalg.norm(v)
    return v/n if n > 1e-6 else np.array([1,0], dtype=np.float32)


def alpha_blend(base, layer, alpha):
    a = np.clip(alpha[...,None], 0, 1)
    return np.clip(base.astype(np.float32)*(1-a) + layer.astype(np.float32)*a, 0, 255).astype(np.uint8)


def draw_stroke_layer(shape, hull, centers, thickness, style, hair_color, side):
    h, w = shape[:2]
    layer = np.zeros((h,w,3), np.uint8)
    alpha = np.zeros((h,w), np.float32)
    rng = np.random.default_rng(abs(hash(style['id'] + side)) % (2**32))
    brow_h = max(8.0, float(np.max(hull[:,1]) - np.min(hull[:,1])))
    brow_w = max(20.0, float(np.max(hull[:,0]) - np.min(hull[:,0])))
    count = int(180 + brow_w*0.25 + style['density']*120)
    clip = np.zeros((h,w), np.uint8)
    cv2.fillConvexPoly(clip, cv2.convexHull(hull.astype(np.int32)), 255)
    clip = cv2.GaussianBlur(cv2.dilate(clip, np.ones((3,3), np.uint8), iterations=1), (0,0), 0.8)

    body = np.array([max(8, hair_color[0]*0.72), max(10, hair_color[1]*0.72), max(12, hair_color[2]*0.72)], dtype=np.float32)
    head = np.array([min(170, body[0]+18), min(150, body[1]+14), min(135, body[2]+10)], dtype=np.float32)
    tailc = np.array([max(4, body[0]-10), max(6, body[1]-10), max(8, body[2]-10)], dtype=np.float32)

    # soft under shadow on transparent layer
    shadow = np.zeros_like(layer)
    cv2.polylines(shadow, [cv2.convexHull(hull.astype(np.int32))], True, tuple(map(int, body)), 1, cv2.LINE_AA)
    shadow = cv2.GaussianBlur(shadow, (0,0), max(1.2, brow_h*0.08))
    layer = cv2.addWeighted(layer, 1.0, shadow, 0.08, 0)
    alpha += (clip.astype(np.float32)/255.0) * 0.04

    for i in range(count):
        t = (i + rng.random()*0.15) / max(1, count-1)
        zone = 'head' if t < 0.22 else 'tail' if t > 0.78 else 'body'
        c = sample_curve(centers, t)
        tan = tangent(centers, t)
        tang = np.arctan2(tan[1], tan[0])
        zone_bias = -0.68 if zone == 'head' else 0.08 if zone == 'tail' else -0.08
        jitter = rng.normal(0, 0.08)
        angle = tang + zone_bias + jitter
        gate = 0.55 if zone == 'head' else 0.62 if zone == 'tail' else 0.92
        if rng.random() > gate * style['density']:
            continue

        idx = min(len(thickness)-1, int(round(t*(len(thickness)-1))))
        normal_offset = rng.uniform(-0.22, 0.22) * thickness[idx]
        root = np.array([c[0] + np.sin(angle + np.pi/2)*normal_offset, c[1] - np.cos(angle + np.pi/2)*normal_offset], dtype=np.float32)
        base_len = brow_h*(0.45 if zone == 'head' else 0.52 if zone == 'tail' else 0.72)
        length = base_len * rng.uniform(0.7, 1.15)
        tip = root + np.array([np.cos(angle)*length, np.sin(angle)*length], dtype=np.float32)
        ctrl = root + (tip-root)*0.46 + np.array([np.cos(angle-0.9), np.sin(angle-0.9)], dtype=np.float32)*length*0.08

        color = head if zone == 'head' else tailc if zone == 'tail' else body
        width = max(1, int((1.0 if zone == 'body' else 0.8) * rng.uniform(0.8, 1.2) * style['thickness']))
        stroke_alpha = (0.18 if zone == 'head' else 0.26 if zone == 'tail' else 0.34) * style['opacity']

        temp = np.zeros_like(layer)
        cv2.line(temp, tuple(root.astype(int)), tuple(ctrl.astype(int)), tuple(map(int, color)), width, cv2.LINE_AA)
        cv2.line(temp, tuple(ctrl.astype(int)), tuple(tip.astype(int)), tuple(map(int, color)), max(1, width-1), cv2.LINE_AA)
        mask = cv2.cvtColor(temp, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        mask *= (clip.astype(np.float32)/255.0) * stroke_alpha
        alpha = np.maximum(alpha, mask * 0.9)
        layer = alpha_blend(layer, temp, mask)

    # fine detail pass
    for i in range(int(count*0.28)):
        t = rng.uniform(0.08, 0.92)
        c = sample_curve(centers, t)
        tan = tangent(centers, t)
        ang = np.arctan2(tan[1], tan[0]) + rng.normal(0, 0.05)
        idx = min(len(thickness)-1, int(round(t*(len(thickness)-1))))
        root = np.array([c[0], c[1] + rng.uniform(-0.14, 0.14)*thickness[idx]], dtype=np.float32)
        tip = root + np.array([np.cos(ang)*brow_h*rng.uniform(0.18,0.28), np.sin(ang)*brow_h*rng.uniform(0.18,0.28)], dtype=np.float32)
        temp = np.zeros_like(layer)
        cv2.line(temp, tuple(root.astype(int)), tuple(tip.astype(int)), tuple(map(int, body)), 1, cv2.LINE_AA)
        mask = cv2.cvtColor(temp, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        mask *= (clip.astype(np.float32)/255.0) * 0.12
        alpha = np.maximum(alpha, mask * 0.8)
        layer = alpha_blend(layer, temp, mask)

    return layer, np.clip(alpha, 0, 1)


def render_style(clean, left_hull, right_hull, style, hair_color):
    result = clean.copy()
    for hull, side in [(left_hull, 'left'), (right_hull, 'right')]:
        centers, thickness = hull_curve(hull, side)
        centers, thickness = stylize_curve(centers, thickness, style)
        layer, alpha = draw_stroke_layer(clean.shape, hull, centers, thickness, style, hair_color, side)
        result = alpha_blend(result, layer, alpha)
    return result


def panel_label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0,0), (out.shape[1], 46), (22,22,22), -1)
    cv2.putText(out, text, (14, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (255,255,255), 2, cv2.LINE_AA)
    return out


def main():
    img = cv2.imread(str(SRC))
    landmarks = load_landmarks()
    skin_mask, brow_inner, brow_soft, left_hull, right_hull, face_hull = build_masks(img, landmarks)
    clean = c3_remove(img, skin_mask, brow_inner, brow_soft)
    hair = sample_hair_color(img, face_hull)

    results = []
    for style in STYLES:
        res = render_style(clean, left_hull, right_hull, style, hair)
        results.append((style, res))
        cv2.imwrite(str(OUT_DIR / f"{style['id']}.png"), res)

    overlay = img.copy()
    cv2.polylines(overlay, [left_hull.astype(np.int32)], True, (0,0,255), 2)
    cv2.polylines(overlay, [right_hull.astype(np.int32)], True, (255,0,0), 2)
    tiles = [panel_label(img, 'original'), panel_label(clean, 'C3 clean'), panel_label(overlay, 'landmarks/hulls')]
    tiles += [panel_label(res, f"{i+1}. {style['name']}") for i, (style, res) in enumerate(results)]
    grid = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:6])])
    cv2.imwrite(str(OUT_DIR / 'sample_top3_grid_v2.png'), grid)
    print({'out_dir': str(OUT_DIR), 'styles': [s['id'] for s, _ in results]})

if __name__ == '__main__':
    main()
