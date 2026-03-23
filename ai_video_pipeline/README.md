# AI Shorts Pipeline (Local-first, no browser automation)

목표: **비용 0원**, **최대한 자동화**, **쇼츠(9:16) 자동 생성**

## v0 동작 방식
1. 아이디어 생성 (`scripts/generate_ideas.py`)
2. 에피소드 스펙 생성 (`scripts/make_episode_spec.py`)
3. 로컬 영상 생성(ComfyUI API 사용, 실패 시 더미 클립)
4. ffmpeg로 합본 + 자막 + 메타데이터 출력

## 빠른 시작
```bash
cd ai_video_pipeline
bash scripts/setup_local.sh
python3 scripts/generate_ideas.py --count 3
python3 scripts/make_episode_spec.py --topic "사람이 우주에 맨몸으로 가면" --seconds 45
python3 scripts/render_episode.py --spec output/latest_episode.json
```

결과물:
- `output/final.mp4`
- `output/title_candidates.txt`
- `output/description.txt`
- `output/tags.txt`
- `output/upload_checklist.md`

## ComfyUI 연결
- 기본 엔드포인트: `http://127.0.0.1:8188`
- `config/pipeline.json`의 `comfy_api` 및 `workflow_path` 수정 가능

## Wan 2.1 Mac 시도 경로
32GB unified memory Mac 기준 권장 조합:
- `city96/Wan2.1-I2V-14B-480P-gguf` 의 `Q4_K_M`
- `Comfy-Org/Wan_2.1_ComfyUI_repackaged` 의 fp8 text encoder + clip vision + vae
- custom node: `ComfyUI-GGUF`

설치:
```bash
cd ai_video_pipeline
bash scripts/setup_wan_mac.sh
```

메모:
- full fp16 Wan 14B는 Mac에서 사실상 무겁다
- 먼저 480p / 짧은 클립으로 안정성 확인 후 업스케일하는 쪽이 현실적이다

## 크론 예시 (매일 10:00 아이디어)
```cron
0 10 * * * cd /Users/gimdoi/.openclaw/workspace/ai_video_pipeline && /usr/bin/python3 scripts/generate_ideas.py --count 3 >> output/cron.log 2>&1
```

## 주의
- 브라우저 자동 업로드는 현재 권한 없이 제외
- 업로드는 수동, 메타데이터는 자동 생성
