---
title: "OpenClaw Slack bot 이미지 업로드 실패 원인과 해결"
date: 2026-03-20 15:55:00 +0900
categories: [trouble]
tags: [openclaw, slack-bot, image-upload, workspace, localmediaaccesserror]
---

OpenClaw를 연결한 Slack bot이 계속 파일 업로드에 실패했다.

![OpenClaw Slack Error](/assets/images/2026-03-20-openclaw-slack-bot-upload-failure_001.png)

 이미지 첨부가 실패한 원인은 로컬 미디어 업로드 전 경로 검증이 허용된 기본 디렉터리만 통과시키기 때문이다.
workspace를 임의 경로로 바꿔 사용하면서, 생성 이미지가 OpenClaw가 허용한 로컬 업로드 경로 밖으로 판정되어 첨부에 실패했다.

```
[slack] final reply failed: LocalMediaAccessError: Local media path is not under an allowed directory: /Users/gimdoi/.openclaw/user_workspace/out/latest_20260320_131254/nano_person_segmented.png
```

관련 코드는 다음 위치에 있다.
- `src/media/local-roots.ts`
  로컬 미디어 업로드 시 허용하는 기본 루트 목록을 정의한다.
  - `OpenClaw temp dir`
  - `<stateDir>/media`
  - `<stateDir>/agents`
  - `<stateDir>/workspace`
  - `<stateDir>/sandboxes`
  - 추가로 agent ID가 있으면 resolveAgentWorkspaceDir(cfg, agentId) 결과도 포함한다.

- `src/media/web-media.ts`
  - assertLocalMediaAllowed()에서 로컬 파일 경로를 realpath 기준으로 검사하고, 허용 루트 밖이면 LocalMediaAccessError를 발생시킨다.

![OpenClaw Slack Fixed](/assets/images/2026-03-20-openclaw-slack-bot-upload-failure_002.png)

허용된 workspace 경로로 workspace를 변경한 뒤 안에 생성된 파일은 Slack bot이 정상적으로 이미지 첨부 전송할 수 있었다.
