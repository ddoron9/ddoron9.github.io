# Wan 2.1 Mac Plan

## Target
- Model: Wan 2.1 I2V 14B 480p
- Mac profile: GGUF Q4_K_M + fp8 text encoder
- Goal: 5~8s vertical clip from a strong key image

## Required files
- `models/unet/wan2.1-i2v-14b-480p-Q4_K_M.gguf`
- `models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `models/clip_vision/clip_vision_h.safetensors`
- `models/vae/wan_2.1_vae.safetensors`
- custom node: `custom_nodes/ComfyUI-GGUF`

## Why this profile
- 32GB unified memory Mac cannot realistically hold full fp16 Wan 14B.
- Q4_K_M keeps quality decent while fitting local constraints better.
- 480p first, then upscale / interpolate later.

## First-test settings
- Resolution: 480p base
- Frames: 49~65
- FPS: 8~12
- Steps: 18~24
- Guidance: 4.5~6.0
- Start from one strong key image per scene

## Failure signs
- `M1 buffer is not large enough`
- ComfyUI hang at model load
- Swap explosion / system slowdown

## Fallback
- Keep Mac for key-image generation and workflow preview
- Use external GPU only for final Wan render
