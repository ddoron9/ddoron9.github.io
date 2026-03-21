# TOOLS.md - Local Ops Notes

## Agent Runtime Notes

### Codex
- Main config path: `~/.codex/config.toml`
- Current policy: low-cost default, escalate only by trigger
- Never include `~/.codex/auth.json` in uploads

### OpenClaw
- Main config path: `~/.openclaw/openclaw.json`
- For sharing: always create redacted copy first
- Jobs channel intent: job scouting + application support only

## Safe Share Checklist (before uploading config)

- Remove API keys / tokens / secrets
- Exclude personal DB/session files
- Include only purpose-fit files (e.g., config.toml, AGENTS.md)
- Add one-line note: "sensitive values redacted"

## Packaging snippets

```bash
# codex only
zip -r out/codex-config-only.zip out/codex-config-only

# openclaw md only
zip -r out/openclaw-md-pack.zip out/openclaw-md-pack
```
