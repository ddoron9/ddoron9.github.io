#!/usr/bin/env python3
from pathlib import Path
import argparse
import imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import torch
from diffusers import StableVideoDiffusionPipeline


def make_start_image(width=320, height=576):
    img = Image.new('RGB', (width, height), '#02040a')
    d = ImageDraw.Draw(img)

    for i in range(height):
        c = int(5 + 20 * (i / height))
        d.line((0, i, width, i), fill=(c, c + 5, c + 15))

    rng = np.random.default_rng(42)
    star_count = max(80, (width * height) // 2500)
    for _ in range(star_count):
        x = int(rng.integers(0, width))
        y = int(rng.integers(0, height))
        r = int(rng.integers(1, 2))
        b = int(rng.integers(180, 255))
        d.ellipse((x-r, y-r, x+r, y+r), fill=(b, b, b))

    d.ellipse((-width // 5, height - height // 4, width + width // 5, height + height // 6), fill=(20, 90, 180))
    img = img.filter(ImageFilter.GaussianBlur(radius=4))
    d = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2 + height // 20
    body_w = width // 10
    head_r = width // 16
    d.ellipse((cx - body_w - 15, cy - height // 7, cx + body_w + 15, cy - height // 15), fill=(220, 225, 235))
    d.ellipse((cx - head_r, cy - height // 4, cx + head_r, cy - height // 6), fill=(235, 240, 245))
    d.rectangle((cx - body_w, cy - height // 6, cx + body_w, cy + height // 20), fill=(225, 230, 240))
    d.rectangle((cx - body_w * 2, cy - height // 7, cx - body_w, cy - height // 10), fill=(225, 230, 240))
    d.rectangle((cx + body_w, cy - height // 7, cx + body_w * 2, cy - height // 10), fill=(225, 230, 240))
    d.rectangle((cx - body_w + 5, cy + height // 20, cx - 4, cy + height // 7), fill=(225, 230, 240))
    d.rectangle((cx + 4, cy + height // 20, cx + body_w - 5, cy + height // 7), fill=(225, 230, 240))
    d.rounded_rectangle((cx - body_w // 2, cy - height // 4 + 10, cx + body_w // 2, cy - height // 6), radius=10, fill=(70, 120, 180))
    return img


def export_to_video(frames, path, fps=6):
    arrs = [np.array(f) for f in frames]
    imageio.mimsave(path, arrs, fps=fps, quality=8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--frames', type=int, default=8)
    ap.add_argument('--width', type=int, default=320)
    ap.add_argument('--height', type=int, default=576)
    ap.add_argument('--fps', type=int, default=6)
    ap.add_argument('--steps', type=int, default=12)
    ap.add_argument('--decode-chunk-size', type=int, default=1)
    ap.add_argument('--motion-bucket-id', type=int, default=48)
    ap.add_argument('--noise-aug-strength', type=float, default=0.05)
    ap.add_argument('--device', choices=['auto', 'mps', 'cpu'], default='auto')
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = make_start_image(width=args.width, height=args.height)
    img.save(out.parent / 'svd_start.png')

    if args.device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    else:
        device = args.device
    dtype = torch.float16 if device == 'mps' else torch.float32

    pipe = StableVideoDiffusionPipeline.from_pretrained(
        'stabilityai/stable-video-diffusion-img2vid-xt-1-1',
        torch_dtype=dtype,
        variant='fp16' if device == 'mps' else None,
    )
    pipe.enable_attention_slicing()
    try:
        pipe.enable_vae_slicing()
    except Exception:
        pass
    try:
        pipe.enable_model_cpu_offload()
    except Exception:
        pipe = pipe.to(device)
    else:
        if device == 'cpu':
            pipe = pipe.to(device)

    generator = torch.manual_seed(42)
    result = pipe(
        img,
        decode_chunk_size=args.decode_chunk_size,
        generator=generator,
        motion_bucket_id=args.motion_bucket_id,
        noise_aug_strength=args.noise_aug_strength,
        num_frames=args.frames,
        num_inference_steps=args.steps,
        min_guidance_scale=1.0,
        max_guidance_scale=1.5,
    )
    frames = result.frames[0]
    export_to_video(frames, str(out), fps=args.fps)
    print(f'[ok] wrote {out}')


if __name__ == '__main__':
    main()
