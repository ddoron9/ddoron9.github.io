#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMFY="$ROOT/vendor/ComfyUI"
VENV="$COMFY/.venv/bin/python"
MODELS="$COMFY/models"

if [ ! -x "$VENV" ]; then
  echo "[error] ComfyUI venv not found: $VENV" >&2
  exit 1
fi

mkdir -p "$MODELS/unet" "$MODELS/text_encoders" "$MODELS/clip_vision" "$MODELS/vae"

if [ ! -d "$COMFY/custom_nodes/ComfyUI-GGUF" ]; then
  echo "[setup] cloning ComfyUI-GGUF"
  git clone https://github.com/city96/ComfyUI-GGUF.git "$COMFY/custom_nodes/ComfyUI-GGUF"
fi

"$VENV" -m pip install -q --upgrade gguf sentencepiece protobuf huggingface_hub

echo "[setup] downloading Wan 2.1 Mac profile (Q4_K_M + fp8 text encoder)"
"$VENV" - <<'PY'
from pathlib import Path
from huggingface_hub import hf_hub_download

root = Path('''/Users/gimdoi/.openclaw/workspace/ai_video_pipeline/vendor/ComfyUI/models''')
files = [
    ('city96/Wan2.1-I2V-14B-480P-gguf', 'wan2.1-i2v-14b-480p-Q4_K_M.gguf', root/'unet'/'wan2.1-i2v-14b-480p-Q4_K_M.gguf'),
    ('Comfy-Org/Wan_2.1_ComfyUI_repackaged', 'split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors', root/'text_encoders'/'umt5_xxl_fp8_e4m3fn_scaled.safetensors'),
    ('Comfy-Org/Wan_2.1_ComfyUI_repackaged', 'split_files/clip_vision/clip_vision_h.safetensors', root/'clip_vision'/'clip_vision_h.safetensors'),
    ('Comfy-Org/Wan_2.1_ComfyUI_repackaged', 'split_files/vae/wan_2.1_vae.safetensors', root/'vae'/'wan_2.1_vae.safetensors'),
]
for repo, filename, local in files:
    local.parent.mkdir(parents=True, exist_ok=True)
    if local.exists() and local.stat().st_size > 0:
        print(f'[skip] {local.name}')
        continue
    path = hf_hub_download(repo_id=repo, filename=filename)
    local.write_bytes(Path(path).read_bytes())
    print(f'[ok] {local}')
PY

echo "[done] Wan 2.1 Mac profile ready"
