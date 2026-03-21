#!/usr/bin/env python3
from pathlib import Path
import argparse, json, random


def build_scene_prompts(topic: str):
    return [
        f"Cinematic hook about: {topic}, dramatic opening, 9:16 vertical, realistic science style",
        f"Scientific explanation scene 1 for: {topic}, clean visual storytelling, 9:16",
        f"Scientific explanation scene 2 for: {topic}, motion and depth, 9:16",
        f"Scientific explanation scene 3 for: {topic}, no gore, documentary tone, 9:16",
        f"Critical moment and consequence for: {topic}, realistic visuals, 9:16",
        f"Future insight ending for: {topic}, hopeful, cinematic, 9:16",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', required=True)
    ap.add_argument('--seconds', type=int, default=45)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    out = root / 'output'
    out.mkdir(parents=True, exist_ok=True)

    scenes = [{
        'index': i + 1,
        'seconds': max(5, args.seconds // 6),
        'seed': random.randint(1, 99999999),
        'prompt': p
    } for i, p in enumerate(build_scene_prompts(args.topic))]

    spec = {
        'topic': args.topic,
        'total_seconds': args.seconds,
        'voiceover': f"{args.topic}를 과학적으로 45초 안에 설명하는 내레이션",
        'scenes': scenes,
        'meta': {
            'titles': [
                f"{args.topic}: 45초 사고실험",
                f"{args.topic}, 실제로 가능할까?",
                f"{args.topic}의 과학적 결말"
            ],
            'tags': ["과학", "사고실험", "미래", "우주", "shorts"]
        }
    }

    p = out / 'latest_episode.json'
    p.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[ok] wrote {p}")


if __name__ == '__main__':
    main()
