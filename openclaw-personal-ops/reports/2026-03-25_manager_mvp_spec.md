# Manager bot MVP spec

## Goal

Create a Slack-facing `manager` mode that keeps assigning safe follow-up work to OpenClaw when Doyi is away, using prior direction from recent conversation, workspace memory, and existing repo state.

## Scope

`manager` is for **research** and **video** work only.

Allowed by default:
- follow-up task decomposition
- experiment planning and next-step sequencing
- code/doc/test edits inside the workspace
- local execution and report generation
- GitHub push **only if no secrets, tokens, keys, or personal data are included**
- downloads of libraries, packages, checkpoints, and model weights

Blocked unless explicitly approved:
- handling or transmitting secrets, tokens, API keys, auth files
- sending or uploading personal information
- emailing, posting, messaging, or other external sends with user data
- deleting user data or destructive cleanup
- infra / permission / billing changes
- downloading PDFs or general user documents from external sources

## Trigger model

Manager mode is opt-in and time-bounded.

Example trigger phrases:
- `이제부터 3시간 manager`
- `몇 시간 동안 맡아`
- `manager on 4h`
- `지금부터 manager 모드`

Expected behavior after trigger:
1. Doyi gives initial task to `doyiclaw`.
2. `doyiclaw` responds once with the immediate result.
3. For the active window, `manager` continues with follow-up planning, next actions, and progress updates.
4. Reports should go to the **channel**, not as thread-only follow-ups.

## Follow-up decision policy

When `manager` takes over, it should:
1. Read the latest user goal and the last completed assistant output.
2. Infer the most useful next step within the same workstream.
3. Prefer work that unblocks future tasks or reduces waiting.
4. Stop and ask when the next step crosses a guardrail.

Priority order:
1. unblock current research/video pipeline
2. prepare the next runnable artifact (prompt, script, config, checklist, report)
3. summarize findings and propose the next bounded step

## Safety filters

Before any external push/upload/download, check:
- Does the content include tokens, keys, cookies, session files, auth blobs?
- Does it include Doyi's personal info, account details, resume raw docs, PDFs, or private application files?
- Is the download a code/library/model-weight dependency rather than a user document?

If any answer is risky, do not proceed automatically.

## Suggested implementation pieces

### 1. State file
Track manager mode in a file such as:

```json
{
  "enabled": false,
  "startedAt": null,
  "until": null,
  "scope": ["research", "video"],
  "reportChannel": "#ops",
  "lastDelegatedFrom": null
}
```

### 2. Prompt layer
Use a dedicated `manager` prompt that:
- inherits workspace memory and current channel context
- continues only safe follow-up work
- writes concise channel updates
- never pretends approval exists for blocked actions

### 3. Reporting format
Recommended channel update format:
- `manager 시작: 범위 / 종료시각 / 차단규칙`
- `manager 진행: 지금 한 일 / 다음 일 / 막힌 것`
- `manager 종료: 결과 / 남은 리스크 / 사람 확인 필요사항`

## First MVP deliverables

1. a manager policy file under `state/manager/`
2. a reusable manager prompt under `prompts/`
3. a lightweight runner or cron bridge that checks whether manager mode is active
4. channel-first update formatting

## Explicit policy captured from Doyi

- External send is allowed **only when the payload contains no token, key, or personal information**.
- GitHub push is allowed, but secret leakage must be checked carefully.
- Downloads are limited to things like libraries and model weights.
- PDF and similar document downloads are not allowed in manager autopilot.
- Manager should activate only after Doyi explicitly turns it on for a bounded number of hours.
