# openresearch-character-consistency

Apple Silicon(M1 Pro 32GB) 로컬 환경에서 reference-based character consistency 파이프라인을 비교/기록하는 오픈리서치 레포.

## Research Question

로컬/저비용 환경에서 같은 캐릭터를 여러 장면에 일관되게 유지하는 가장 실용적인 파이프라인은 무엇인가?

## Initial Scope

- Hardware: MacBook Pro M1 Pro, 32GB RAM
- Cost: 0원, 로컬 우선
- Task: character-consistent image generation across multiple scenes
- Primary comparison:
  - SDXL + IP-Adapter
  - SDXL + ControlNet
  - SDXL + IP-Adapter + ControlNet
  - SDXL + lightweight LoRA (optional later)

## Repo Structure

- `reading/`: papers / model notes
- `questions/`: research questions and hypotheses
- `benchmarks/`: prompts, scene sets, evaluation rubric
- `experiments/`: per-run experiment logs
- `results/`: outputs and summarized observations
- `reports/`: weekly or milestone summaries
- `templates/`: reusable experiment / paper note templates

## First Milestone

1. Define a fixed character brief
2. Define 5 target scenes
3. Reproduce baseline generations
4. Compare consistency / runtime / failure modes
5. Publish report with practical recommendation

## Evaluation Axes

- Face identity consistency
- Outfit / color consistency
- Prompt adherence
- Pose / scene flexibility
- Generation time
- Memory pressure
- Failure modes

## Next Actions

1. Fill `benchmarks/scene_set_v1.md`
2. Fill `questions/research-plan-v1.md`
3. Run baseline experiment logs in `experiments/`
4. Summarize results in `reports/`

## GitHub Publish Plan

결과 정리 후 아래 순서로 공개:

1. 민감정보/대용량 파일 제거
2. README에 목적/세팅/재현법 정리
3. 대표 결과 이미지/표 정리
4. GitHub repo push
