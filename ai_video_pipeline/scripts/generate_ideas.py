#!/usr/bin/env python3
from pathlib import Path
import argparse, datetime

IDEAS = [
    "사람이 우주에 맨몸으로 가면 10초 동안 무슨 일이 생길까",
    "블랙홀 근처 1시간이 지구에서는 몇 년일까",
    "빛보다 빠르면 원인과 결과는 왜 꼬일까",
    "시간여행이 가능하면 할아버지 역설은 어떻게 풀릴까",
    "인간 뇌-칩 연결이 보편화되면 직업은 어떻게 바뀔까",
    "우주 엘리베이터가 실제로 가능하려면 무엇이 필요할까",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=3)
    args = ap.parse_args()

    out_dir = Path(__file__).resolve().parents[1] / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = IDEAS[:max(1, args.count)]

    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [f"[IDEA] {ts}"] + [f"{i+1}. {x}" for i, x in enumerate(selected)]
    txt = "\n".join(lines) + "\n"

    (out_dir / 'ideas_latest.txt').write_text(txt, encoding='utf-8')
    print(txt)


if __name__ == '__main__':
    main()
