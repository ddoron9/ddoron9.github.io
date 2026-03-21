#!/usr/bin/env python3
from pathlib import Path
import argparse, json, math, random, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT_CANDIDATES = [
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    '/System/Library/Fonts/Supplemental/Verdana Bold.ttf',
]

SCENE_TEXTS = [
    ('우주에 맨몸으로', '나가면 바로 얼까?'),
    ('정답은', '즉시 얼지는 않음'),
    ('진짜 문제는', '산소 부족과 압력'),
    ('의식은 대개', '10~15초 안에 흐려짐'),
    ('몸이 폭발하진 않지만', '위험은 매우 큼'),
    ('결론', '보호복 없이는 생존 불가'),
]

PALETTES = [
    ('#050816', '#102c5f', '#7dd3fc'),
    ('#0b1020', '#16345f', '#fca5a5'),
    ('#04131a', '#154360', '#86efac'),
    ('#0f172a', '#312e81', '#c4b5fd'),
    ('#111827', '#7c2d12', '#fdba74'),
    ('#020617', '#0f766e', '#99f6e4'),
]


def pick_font(size: int):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_w):
    words = list(text)
    lines, cur = [], ''
    for ch in words:
        test = cur + ch
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_space_art(img: Image.Image, idx: int, accent: str):
    d = ImageDraw.Draw(img)
    rng = random.Random(100 + idx)
    for _ in range(220):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        r = rng.randint(1, 3)
        b = rng.randint(170, 255)
        d.ellipse((x-r, y-r, x+r, y+r), fill=(b, b, b))

    planet_y = int(H * 0.82)
    d.ellipse((-140, planet_y - 120, W + 140, H + 220), fill='#1d4ed8')
    d.ellipse((80, planet_y - 70, W - 80, H + 120), outline=accent, width=8)

    cx, cy = W // 2, int(H * 0.45)
    suit = '#e5e7eb'
    visor = '#7dd3fc'
    scale = 1 + (idx % 3) * 0.08
    bw = int(90 * scale)
    hr = int(60 * scale)
    d.ellipse((cx-hr, cy-230, cx+hr, cy-110), fill=suit)
    d.rounded_rectangle((cx-bw, cy-120, cx+bw, cy+130), radius=40, fill=suit)
    d.rounded_rectangle((cx-bw-90, cy-80, cx-bw+10, cy-10), radius=25, fill=suit)
    d.rounded_rectangle((cx+bw-10, cy-80, cx+bw+90, cy-10), radius=25, fill=suit)
    d.rounded_rectangle((cx-bw+20, cy+120, cx-10, cy+320), radius=25, fill=suit)
    d.rounded_rectangle((cx+10, cy+120, cx+bw-20, cy+320), radius=25, fill=suit)
    d.rounded_rectangle((cx-40, cy-205, cx+40, cy-145), radius=14, fill=visor)
    if idx in (2, 3, 4):
        for off in range(3):
            y = cy - 40 + off * 42
            d.rounded_rectangle((130, y, W-130, y+14), radius=7, fill=(255,255,255,40))
    if idx == 4:
        d.arc((cx-190, cy-320, cx+190, cy+60), start=210, end=330, fill='#fca5a5', width=10)
    if idx == 5:
        d.ellipse((820, 220, 930, 330), fill='#fde68a')
        for i in range(8):
            ang = i * math.pi / 4
            x1 = 875 + int(math.cos(ang) * 70)
            y1 = 275 + int(math.sin(ang) * 70)
            x2 = 875 + int(math.cos(ang) * 120)
            y2 = 275 + int(math.sin(ang) * 120)
            d.line((x1, y1, x2, y2), fill='#fde68a', width=6)


def make_scene_image(idx: int, title: str, subtitle: str, out_path: Path):
    bg1, bg2, accent = PALETTES[(idx - 1) % len(PALETTES)]
    img = Image.new('RGB', (W, H), bg1)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c1 = tuple(int(int(bg1[i:i+2], 16) * (1 - t) + int(bg2[i:i+2], 16) * t) for i in (1, 3, 5))
        d.line((0, y, W, y), fill=c1)

    draw_space_art(img, idx, accent)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((70, 1060, W - 70, 1650), radius=48, fill=(3, 7, 18, 180))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    d = ImageDraw.Draw(img)

    small = pick_font(44)
    title_font = pick_font(106)
    sub_font = pick_font(74)
    chip = f'SCENE {idx}'
    d.rounded_rectangle((78, 100, 320, 172), radius=28, fill=accent)
    d.text((118, 116), chip, font=small, fill='black')

    title_lines = wrap_text(d, title, title_font, W - 180)
    subtitle_lines = wrap_text(d, subtitle, sub_font, W - 180)
    y = 1120
    for line in title_lines:
        d.text((96, y), line, font=title_font, fill='white', stroke_width=2, stroke_fill='black')
        y += 118
    y += 18
    for line in subtitle_lines:
        d.text((96, y), line, font=sub_font, fill=accent, stroke_width=2, stroke_fill='black')
        y += 92

    footer = '45초 사고실험 · AI 모션 편집 버전'
    d.text((98, 1580), footer, font=small, fill=(220, 225, 235))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)


def run(cmd):
    subprocess.run(cmd, check=True)


def render_clip(img_path: Path, out_path: Path, seconds: int, idx: int):
    fps = 30
    total = max(1, seconds * fps)
    zoom_expr = f"zoompan=z='min(1.0+on*0.0009,1.10)':x='iw/2-(iw/zoom/2)+sin(on/18)*{8 + idx*2}':y='ih/2-(ih/zoom/2)+cos(on/22)*{10 + idx*2}':d={total}:s={W}x{H}:fps={fps}"
    vf = f"{zoom_expr},fade=t=in:st=0:d=0.5,fade=t=out:st={max(seconds-0.6,0)}:d=0.6"
    run(['ffmpeg', '-y', '-loop', '1', '-i', str(img_path), '-vf', vf, '-t', str(seconds), '-pix_fmt', 'yuv420p', '-r', str(fps), str(out_path)])


def concat_clips(clips, out):
    list_file = out.parent / 'concat_list.txt'
    list_file.write_text(''.join([f"file '{c.as_posix()}'\n" for c in clips]), encoding='utf-8')
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(list_file), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(out)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    root = Path(__file__).resolve().parents[1]
    out = root / 'output'
    tmp = root / 'tmp_motion'
    img_dir = tmp / 'images'
    clip_dir = tmp / 'clips'
    out.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    clip_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    for s in spec['scenes']:
        idx = s['index']
        title, subtitle = SCENE_TEXTS[idx - 1] if idx - 1 < len(SCENE_TEXTS) else (spec['topic'], f'장면 {idx}')
        img_path = img_dir / f'scene_{idx:02d}.jpg'
        clip_path = clip_dir / f'scene_{idx:02d}.mp4'
        make_scene_image(idx, title, subtitle, img_path)
        render_clip(img_path, clip_path, int(s['seconds']), idx)
        clips.append(clip_path)

    final = out / 'final_motion.mp4'
    concat_clips(clips, final)
    (out / 'title_candidates.txt').write_text('\n'.join(spec['meta']['titles']) + '\n', encoding='utf-8')
    (out / 'description.txt').write_text(f"{spec['topic']}를 45초 사고실험 스타일로 정리한 세로형 영상입니다.\n", encoding='utf-8')
    (out / 'tags.txt').write_text(','.join(spec['meta']['tags']) + ',ai,shorts\n', encoding='utf-8')
    print(f'[ok] rendered {final}')


if __name__ == '__main__':
    main()
