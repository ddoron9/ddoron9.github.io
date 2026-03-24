# OpenClaw Personal Ops

File-based OpenClaw workspace for:

- Slack channel-first personal assistant flows
- macOS Calendar and Reminders summaries through a paired Mac node
- NAVER Mail triage via Mail.app on the paired Mac node
- Daily job scouting with CSV blocklists
- Browser-assisted form filling from saved profile defaults
- Repo lab runs and summary reports
- Time-bounded `manager` delegation mode for safe research/video follow-up

## Layout

- `AGENTS.md`: operating rules for OpenClaw
- `config/openclaw.reference.json5`: schema-safe reference config
- `prompts/`: reusable task prompts for cron/manual runs
- `scripts/`: local helpers that do not require paid API keys
- `state/`: CSV/JSON source of truth
- `reports/`: generated outputs

## Manual setup still required

- Slack app creation and token copy
- OpenClaw OAuth login for `openai-codex`
- Pairing your Mac as an OpenClaw node
- Tailscale install/login on server and Mac

## First files to fill

- `state/profile/basic.json`
- `state/profile/common_fields.json`
- `state/profile/default_answers.json`
- `state/mail/style_notes.md`
- `state/jobs/applied_companies.csv`
- `state/jobs/blocklist_companies.csv`
tate/jobs/applied_companies.csv`
- `state/jobs/blocklist_companies.csv`
