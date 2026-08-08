# SERVICES.md - StudioYou FY Agent

Every external platform/service this project depends on. Update at session close whenever something changes. Credentials are NEVER stored here, pointer only. Mirrored into the cross-project Notion Platform & Service Registry (`https://app.notion.com/p/dd60c5c5ccda496eb10d58f8db0bc8b6`) at session close per the `dev-session-protocol` skill.

| Service | Category | Purpose | Account / Org ID | Console URL | Subscription / Tier | Renewal | Credential Location | Status | Last Verified |
|---|---|---|---|---|---|---|---|---|---|
| GitHub - studioyou-fy-agent | Other | Source code, CLAUDE.md, handoffs/ | github.com/supercreativepeople | https://github.com/supercreativepeople/studioyou-fy-agent | free | n/a | git credential helper (osxkeychain, remote URL de-tokenized 2026-08-07) | Active | 2026-08-07 |
| LiveKit Cloud | Hosting/Realtime | Voice/video agent runtime — FutureYou conversation rooms | studioyou-futureyou-avatar-749nqz32.livekit.cloud, Agent ID CA_Mnhkjj3mUr7T | cloud.livekit.io | unconfirmed tier | n/a | LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET in .env | Active | not independently re-verified 2026-08-07 |
| Deepgram | AI/API | Speech-to-text (via LiveKit Inference) | via LiveKit credentials | - | pay-as-you-go | n/a | via LIVEKIT_* keys, no separate key | Active | not independently re-verified 2026-08-07 |
| Cartesia | AI/API | Text-to-speech (sonic model, via LiveKit Inference) | via LiveKit credentials | - | pay-as-you-go | n/a | via LIVEKIT_* keys, no separate key | Active | not independently re-verified 2026-08-07 |
| Runway | AI/API | Live avatar video rendering — replaced Tavus as of Session AA | RUNWAYML_API_SECRET / RUNWAY_AVATAR_ID | runwayml.com | unconfirmed | n/a | .env on this repo's Mac path (not Cloud Run — rendering happens in this process) | Active | not independently re-verified 2026-08-07 |
| Anthropic API (shared) | AI/API | Claude — agent conversation logic | console.anthropic.com | console.anthropic.com | pay-as-you-go | n/a | ANTHROPIC_API_KEY in .env | Active | not independently re-verified 2026-08-07 |
| Tavus | AI/API | Legacy avatar provider, env vars retained unused | tavusapi.com | tavusapi.com | unconfirmed | n/a | .env (unused) | Needs Verification | 2026-08-07 |

Note: `.env` in this repo is properly gitignored and was confirmed not tracked in git history as of 2026-08-07.
