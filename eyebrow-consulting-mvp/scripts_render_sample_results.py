from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path('/Users/gimdoi/.openclaw/workspace')
SRC = ROOT / 'eyebrow-consulting-mvp/web/sample.jpg'
MODEL = ROOT / 'out/eyebrow_mediapipe/model/face_landmarker.task'
OUT_DIR = ROOT / 'out/eyebrow_render_results'
OUT_DIR.mkdir(parents=True, exist_ok=True)

STYLES = [
    dict(id='natural_straight_soft', name='내추럴 소프트 스트레이트', shapeFamily='straight', densityTier='light', makeupIntensity=0.18, realismScore=0.92, archLift=0.002, thickness=0.12, tailRise=-0.002, density=0.78, opacity=0.82, innerOffset=0.05, tailExtend=0.012, frontLift=0.002, archBias=0.46),
    dict(id='kbeauty_straight_clean', name='클린 K-스트레이트', shapeFamily='straight', densityTier='medium', makeupIntensity=0.38, realismScore=0.90, archLift=0.004, thickness=0.16, tailRise=0.001, density=0.86, opacity=0.88, innerOffset=0.04, tailExtend=0.02, frontLift=0.001, archBias=0.48),
    dict(id='natural_soft_arch', name='내추럴 소프트 아치', shapeFamily='soft', densityTier='medium', makeupIntensity=0.24, realismScore=0.95, archLift=0.014, thickness=0.17, tailRise=0.007, density=0.84, opacity=0.88, innerOffset=0.04, tailExtend=0.02, frontLift=0.0, archBias=0.51),
    dict(id='balanced_soft_full', name='밸런스드 소프트 풀브로우', shapeFamily='soft', densityTier='full', makeupIntensity=0.42, realismScore=0.91, archLift=0.016, thickness=0.20, tailRise=0.008, density=0.92, opacity=0.92, innerOffset=0.032, tailExtend=0.024, frontLift=-0.001, archBias=0.52),
    dict(id='defined_arch_taper', name='디파인드 테이퍼 아치', shapeFamily='high', densityTier='medium', makeupIntensity=0.48, realismScore=0.89, archLift=0.026, thickness=0.20, tailRise=0.011, density=0.88, opacity=0.92, innerOffset=0.03, tailExtend=0.025, frontLift=-0.002, archBias=0.54),
    dict(id='glam_high_arch', name='글램 하이 아치', shapeFamily='high', densityTier='full', makeupIntensity=0.62, realismScore=0.84, archLift=0.03, thickness=0.22, tailRise=0.012, density=0.95, opacity=0.94, innerOffset=0.028, tailExtend=0.028, frontLift=-0.003, archBias=0.55),
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
    return mask, hull

def build_masks_and_brows(img, landmarks):
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
    ys = face_hull[:,0,1]; xs = face_hull[:,0,0]
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

    return skin_mask, brow_raw, brow_inner, brow_soft, left_hull[:,0,:], right_hull[:,0,:], face_hull[:,0,:]

def skin_field(img, skin_mask, sigma=21):
    masked = img.astype(np.float32).copy()
    masked[skin_mask == 0] = 0
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
    gray_out = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray_skin = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[skin_mask > 0].astype(np.float32)
    target = np.percentile(gray_skin, 38) if len(gray_skin) else gray_out.mean()
    darkness = np.clip((target - gray_out) / 28.0, 0, 1) * alpha
    lift = darkness[...,None] * np.array([4.0, 3.5, 3.0], dtype=np.float32)
    out = np.clip(out.astype(np.float32) + lift, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0,0), 3.0)
    edge_alpha = np.clip((alpha - 0.15) / 0.85, 0, 1)[...,None] * 0.18
    out = np.clip(out.astype(np.float32)*(1-edge_alpha) + blur.astype(np.float32)*edge_alpha, 0, 255).astype(np.uint8)
    out = cv2.bilateralFilter(out, 5, 15, 15)
    base_hp = cv2.subtract(base, cv2.GaussianBlur(base, (0,0), 1.2)).astype(np.float32)
    out = np.clip(out.astype(np.float32) + base_hp * (alpha[...,None] * 0.22), 0, 255).astype(np.uint8)
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
    base = sel.mean(axis=0)
    return np.array([np.clip(base[0]*0.84 + 7, 16, 118), np.clip(base[1]*0.86 + 6, 20, 125), np.clip(base[2]*0.88 + 6, 24, 140)], dtype=np.float32)

def recommend_style(face_hull):
    xs, ys = face_hull[:,0], face_hull[:,1]
    ratio = (xs.max()-xs.min()) / max(1.0, (ys.max()-ys.min()))
    if ratio > 0.83: return 'high'
    if ratio < 0.7: return 'straight'
    return 'soft'

def rank_styles(face_hull, left_hull, right_hull, hair_color):
    pref = recommend_style(face_hull)
    def box(h):
        x,y,w,h2 = cv2.boundingRect(h.astype(np.int32))
        return w,h2
    lw, lh = box(left_hull); rw, rh = box(right_hull)
    brow_span = (lw+rw)/2; brow_thick = (lh+rh)/2
    xs, ys = face_hull[:,0], face_hull[:,1]
    face_ratio = (xs.max()-xs.min()) / max(1.0, (ys.max()-ys.min()))
    darkness = (255 - (hair_color[2]*0.2126 + hair_color[1]*0.7152 + hair_color[0]*0.0722)) / 255
    densityTarget = 'full' if darkness > 0.62 else 'medium' if darkness > 0.45 else 'light'
    scored = []
    for s in STYLES:
        shapeFit = 1 if s['shapeFamily']==pref else (0.82 if pref=='soft' and s['shapeFamily']!='high' else 0.64)
        densityFit = 1 if s['densityTier']==densityTarget else (0.85 if s['densityTier']=='medium' and densityTarget!='medium' else 0.7)
        thicknessRatio = brow_thick / max(1, brow_span)
        makeupTarget = 0.48 if face_ratio > 0.82 else 0.22 if face_ratio < 0.72 else 0.34
        browFit = 1 - min(0.55, abs(s['thickness'] - thicknessRatio * 2.5))
        score = shapeFit*0.34 + densityFit*0.18 + s['realismScore']*0.22 + browFit*0.16 + (1-abs(s['makeupIntensity']-makeupTarget))*0.1
        scored.append((score, s))
    return [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)]

def hull_to_curve(hull, side='left'):
    pts = hull[np.argsort(hull[:,0])]
    if side == 'left':
        pts = pts[::-1]
    buckets = np.array_split(pts, min(6, len(pts)))
    centers=[]; tops=[]; bots=[]
    for b in buckets:
        xs=b[:,0]; ys=b[:,1]
        x=float(xs.mean()); tops.append(float(ys.min())); bots.append(float(ys.max())); centers.append((x, float((ys.min()+ys.max())/2)))
    centers=np.array(centers, np.float32)
    thickness=np.maximum(3.0, np.array(bots)-np.array(tops)+1.0)
    return centers, thickness

def stylize_curve(centers, thickness, s):
    n=len(centers)
    out=centers.copy(); th=thickness.copy()
    y_span = float(np.ptp(centers[:,1]))
    for i in range(n):
        t=i/max(1,n-1)
        arch=np.exp(-((t-s['archBias'])/0.2)**2)
        front=max(0,1-t/0.26)
        tail=max(0,(t-0.54)/0.46)
        out[i,1] += y_span*0.12 - y_span*(s['archLift']*0.34*arch + s['frontLift']*0.18*front + s['tailRise']*0.14*tail)
        th[i] *= (0.92 + s['thickness']*1.36) * (0.76 + (1-abs(t-0.46)*1.35)*0.18) * (0.64 + min(1,t*3)*0.2) * (1-max(0,t-0.72)*0.48)
    return out, np.maximum(2.5, th)

def sample_curve(curve, t):
    if len(curve)==1: return curve[0]
    x = t*(len(curve)-1)
    i=min(len(curve)-2, int(x)); a=x-i
    return curve[i]*(1-a)+curve[i+1]*a

def tangent(curve, t):
    p0=sample_curve(curve, max(0,t-0.03)); p1=sample_curve(curve, min(1,t+0.03))
    v=p1-p0; n=np.linalg.norm(v)
    return v/n if n>1e-6 else np.array([1.0,0.0], np.float32)

def mix(c1, c2, r):
    return c1*(1-r)+c2*r

def draw_styled_brow(img, hull, style, hair_color, side='left'):
    out = img.copy()
    overlay = out.copy()
    centers, thickness = hull_to_curve(hull, side)
    centers, thickness = stylize_curve(centers, thickness, style)
    body_color = mix(hair_color, np.array([18,20,24], np.float32), 0.08 + style['makeupIntensity']*0.04)
    head_color = mix(hair_color, np.array([118,132,154], np.float32), 0.18)
    tail_color = mix(hair_color, np.array([8,8,10], np.float32), 0.12 + style['makeupIntensity']*0.05)
    xs, ys = hull[:,0], hull[:,1]
    brow_box_h = max(8.0, ys.max()-ys.min())
    brow_box_w = max(20.0, xs.max()-xs.min())
    strand_count = int(220 + brow_box_w*0.42 + style['density']*150 + style['makeupIntensity']*70)

    poly = cv2.convexHull(hull.astype(np.int32))
    clipmask = np.zeros(out.shape[:2], np.uint8)
    cv2.fillConvexPoly(clipmask, poly, 255)
    clipmask = cv2.dilate(clipmask, np.ones((5,5), np.uint8), iterations=1)
    clipmask = cv2.GaussianBlur(clipmask, (0,0), 1.0)

    # shadow
    shadow = np.zeros_like(out)
    cv2.fillConvexPoly(shadow, poly, (int(body_color[0]), int(body_color[1]), int(body_color[2])))
    shadow = cv2.GaussianBlur(shadow, (0,0), max(1.0, brow_box_h*0.1))
    alpha_shadow = (0.08 + style['opacity']*0.08) * (clipmask.astype(np.float32)/255.0)[...,None]
    overlay = np.clip(overlay.astype(np.float32)*(1-alpha_shadow) + shadow.astype(np.float32)*alpha_shadow, 0,255).astype(np.uint8)

    rng = np.random.default_rng(abs(hash(style['id'] + side)) % (2**32))
    for i in range(strand_count):
        t = i / max(1, strand_count-1)
        zone = 'head' if t < 0.22 else 'tail' if t > 0.78 else 'body'
        center = sample_curve(centers, t)
        tan = tangent(centers, t)
        tanang = np.arctan2(tan[1], tan[0])
        zoneBias = -0.82 if zone=='head' else 0.16 if zone=='tail' else -0.18
        jitter = np.sin((t + 0.137) * 38.7) * 0.16 + np.cos((t + 0.137) * 21.3) * 0.06 + rng.normal(0, 0.03)
        angle = tanang + zoneBias + jitter
        densityGate = 0.56 if zone=='head' else 0.64 if zone=='tail' else 0.94
        pr = rng.random()
        if pr > densityGate * style['density']:
            continue
        normalOffset = (pr - 0.5) * brow_box_h * (0.42 if zone=='body' else 0.34)
        root = np.array([center[0] + np.sin(angle + np.pi/2)*normalOffset, center[1] - np.cos(angle + np.pi/2)*normalOffset], np.float32)
        lenBase = brow_box_h*0.55 if zone=='head' else brow_box_h*0.6 if zone=='tail' else brow_box_h*0.82
        length = lenBase * (0.75 + pr*0.55)
        width = max(1, int((0.72 if zone=='tail' else 0.8 if zone=='head' else 1.0) * (0.5 + pr*0.6) + style['makeupIntensity']*0.35))
        tip = np.array([root[0] + np.cos(angle)*length, root[1] + np.sin(angle)*length], np.float32)
        ctrl = np.array([root[0]*(1-0.46)+tip[0]*0.46 + np.cos(angle-0.8)*length*0.12, root[1]*(1-0.46)+tip[1]*0.46 + np.sin(angle-0.8)*length*0.12], np.float32)
        col = head_color if zone=='head' else tail_color if zone=='tail' else body_color
        alpha = (0.22 if zone=='head' else 0.34 if zone=='tail' else 0.42) + style['opacity']*0.26
        stroke = overlay.copy()
        cv2.line(stroke, tuple(root.astype(int)), tuple(ctrl.astype(int)), tuple(map(int,col)), width, cv2.LINE_AA)
        cv2.line(stroke, tuple(ctrl.astype(int)), tuple(tip.astype(int)), tuple(map(int,col)), max(1,width-1), cv2.LINE_AA)
        local = (clipmask.astype(np.float32)/255.0 * alpha)[...,None]
        overlay = np.clip(overlay.astype(np.float32)*(1-local) + stroke.astype(np.float32)*local, 0,255).astype(np.uint8)

    # bottom definition for makeup styles
    if style['makeupIntensity'] > 0.3:
        pts_bottom = []
        for i, c in enumerate(centers):
            t = i/max(1,len(centers)-1)
            off = thickness[i]*0.12
            pts_bottom.append((int(c[0]), int(c[1]+off)))
        cv2.polylines(overlay, [np.array(pts_bottom, np.int32)], False, tuple(map(int, body_color)), 1, cv2.LINE_AA)

    # feather blend only where clip mask
    alpha = (clipmask.astype(np.float32)/255.0)[...,None]
    out = np.clip(img.astype(np.float32)*(1-alpha*0.0) + overlay.astype(np.float32)*(alpha*1.0), 0,255).astype(np.uint8)
    return out

def panel_label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0,0), (out.shape[1], 46), (22,22,22), -1)
    cv2.putText(out, text, (14, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (255,255,255), 2, cv2.LINE_AA)
    return out

def main():
    img = cv2.imread(str(SRC))
    landmarks = load_landmarks()
    skin_mask, brow_raw, brow_inner, brow_soft, left_hull, right_hull, face_hull = build_masks_and_brows(img, landmarks)
    clean = c3_remove(img, skin_mask, brow_inner, brow_soft)
    hair = sample_hair_color(img, face_hull)
    ranked = rank_styles(face_hull, left_hull, right_hull, hair)[:3]

    results=[]
    for style in ranked:
        res = draw_styled_brow(clean, left_hull, style, hair, 'left')
        res = draw_styled_brow(res, right_hull, style, hair, 'right')
        results.append((style, res))
        cv2.imwrite(str(OUT_DIR / f"{style['id']}.png"), res)

    overlay = img.copy()
    cv2.polylines(overlay, [left_hull.astype(np.int32)], True, (0,0,255), 2)
    cv2.polylines(overlay, [right_hull.astype(np.int32)], True, (255,0,0), 2)

    tiles = [panel_label(img, 'original'), panel_label(clean, 'C3 clean'), panel_label(overlay, 'landmarks/hulls')]
    tiles += [panel_label(res, f"{i+1}. {style['name']}") for i, (style, res) in enumerate(results)]
    top = np.hstack(tiles[:3])
    bottom = np.hstack(tiles[3:6]) if len(tiles) >= 6 else np.hstack(tiles[3:])
    grid = np.vstack([top, bottom])
    cv2.imwrite(str(OUT_DIR / 'sample_top3_grid.png'), grid)
    print({'out_dir': str(OUT_DIR), 'top3': [s['id'] for s, _ in results]})

if __name__ == '__main__':
    main()
