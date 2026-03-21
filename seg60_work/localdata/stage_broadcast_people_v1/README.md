# stage_broadcast_people_v1

Initial person-centric pseudo-label subset for `seg60_work`.

## Source status
- Preferred target: copyright-safe/public-domain-friendly local stage/broadcast videos.
- Found locally: `Video-LLaVA/llava/serve/examples/sample_demo_22.mp4`
- Chosen because it is a locally available example clip with a clear stage-performance human subject.
- Caveat: the embedded example asset is **locally available but license is unspecified** (`demo_asset_unspecified`), so it should be treated as an internal bootstrap/demo subset, not a publication-ready release.
- Other locally found videos were mostly title cards, object-only scenes, or non-person footage.

## Pipeline
1. Frame extraction (`extract_every_n=18`)
2. Near-duplicate suppression via 16x16 average hash + Hamming threshold
3. Pseudo-label generation with `yolo11x-seg.pt` person masks
4. Quality filtering by person presence and foreground area ratio
5. Export of SEG60-style manifests + 10-sample audit panel

## Main outputs
- `images/`, `masks/`, `overlays/`
- `manifests/raw_candidates.csv`
- `manifests/filtered_candidates.csv`
- `manifests/seg60_manifest.csv`
- `manifests/seg60_train.csv`
- `manifests/seg60_val.csv`
- `qc/audit_panel_10.png`
- `summary.json`
