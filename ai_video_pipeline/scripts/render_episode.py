#!/usr/bin/env python3
from pathlib import Path
import argparse, json, subprocess


def run(cmd):
    subprocess.run(cmd, check=True)


def make_dummy_clip(path: Path, seconds: int, text: str):
    # fallback clip (검은 배경 + 텍스트)
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f"color=c=black:s=1080x1920:d={seconds}",
        '-vf', f"drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
        '-r', '30',
        str(path)
    ]
    run(cmd)


def concat_clips(clips, out):
    list_file = out.parent / 'concat_list.txt'
    list_file.write_text(''.join([f"file '{c.as_posix()}'\n" for c in clips]), encoding='utf-8')
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(list_file), '-c', 'copy', str(out)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    root = Path(__file__).resolve().parents[1]
    out = root / 'output'
    tmp = root / 'tmp'
    out.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    clips = []
    for s in spec['scenes']:
        cp = tmp / f"scene_{s['index']:02d}.mp4"
        # TODO: ComfyUI API 호출로 교체
        make_dummy_clip(cp, int(s['seconds']), f"scene {s['index']}")
        clips.append(cp)

    final = out / 'final.mp4'
    concat_clips(clips, final)

    (out / 'title_candidates.txt').write_text('\n'.join(spec['meta']['titles']) + '\n', encoding='utf-8')
    (out / 'description.txt').write_text(f"{spec['topic']}를 45초 사고실험으로 설명한 영상입니다.\n", encoding='utf-8')
    (out / 'tags.txt').write_text(','.join(spec['meta']['tags']) + '\n', encoding='utf-8')
    (out / 'upload_checklist.md').write_text(
        "- [ ] final.mp4 확인\n- [ ] 제목 선택\n- [ ] 설명/태그 복붙\n- [ ] 유튜브 수동 업로드\n",
        encoding='utf-8'
    )
    print(f"[ok] rendered {final}")


if __name__ == '__main__':
    main()
