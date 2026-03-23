# Research Plan v1

## Title

Benchmarking reference-based character consistency pipelines on Apple Silicon local hardware

## Problem

단일 캐릭터를 여러 장면/포즈/배경에서 일관되게 유지하는 것은 여전히 어렵다. 특히 Apple Silicon 기반 로컬 환경에서는 모델 선택과 워크플로 제약이 커서 실용적 비교가 부족하다.

## Goal

M1 Pro 32GB 환경에서 가장 실용적인 캐릭터 일관성 파이프라인을 찾고, 재현 가능한 실험 기록을 남긴다.

## Hypotheses

1. 텍스트 프롬프트만 사용하는 baseline보다 reference-based 접근이 consistency를 유의미하게 개선한다.
2. IP-Adapter + ControlNet 조합이 단독 사용보다 일관성과 장면 제어를 동시에 개선한다.
3. 로컬 환경에서는 최고 품질 모델보다 안정적이고 가벼운 파이프라인이 실사용 가치가 높다.

## Baselines

- B0: SDXL prompt-only
- B1: SDXL + IP-Adapter
- B2: SDXL + ControlNet
- B3: SDXL + IP-Adapter + ControlNet
- B4: SDXL + LoRA (optional)

## Fixed Conditions

- Same character brief
- Same scene set
- Same output size per benchmark round
- Same evaluation rubric

## Metrics

### Quantitative-ish
- Runtime per image
- Success rate
- Memory issues / OOM / slowdown

### Qualitative
- Face identity consistency (1-5)
- Outfit consistency (1-5)
- Style consistency (1-5)
- Scene controllability (1-5)
- Overall practical usefulness (1-5)

## Deliverables

- Experiment logs
- Comparison table
- Failure case gallery
- Final practical recommendation
