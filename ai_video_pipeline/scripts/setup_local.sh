#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p output tmp

cat <<'MSG'
[setup] 기본 체크 시작
- python3, ffmpeg 필요
- ComfyUI는 별도 설치(용량 큼)
MSG

if ! command -v python3 >/dev/null 2>&1; then
  echo "[error] python3 없음" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[warn] ffmpeg 없음. 설치 필요 (예: brew install ffmpeg)"
else
  echo "[ok] ffmpeg 확인됨"
fi

python3 - <<'PY'
import json, pathlib
root = pathlib.Path('.').resolve()
print('[ok] pipeline root:', root)
print('[ok] config exists:', (root/'config'/'pipeline.json').exists())
PY

echo "[done] setup skeleton complete"
