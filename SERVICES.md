# SERVICES.md - StudioYou FY Agent

Every external platform/service this project depends on. Update at session close whenever something changes. Credentials are NEVER stored here, pointer only. Mirrored into the cross-project Notion Platform & Service Registry (`https://app.notion.com/p/dd60c5c5ccda496eb10d58f8db0bc8b6`) at session close per the `dev-session-protocol` skill.

## Corporate / billing structure (recorded 2026-08-09)

**Frisson Digital, Inc. is the parent company and owns both StudioYou and SCREENBot.** This supersedes the earlier per-product newco plan (StudioYou Inc., Delaware C-corp, with SCP Inc. as venture studio) still described in `studioyou-backend/CLAUDE.md`. A single parent owning both products aligns with incubator programs, Anthropic's programs, and fundraising opportunities.

**Every billing instance is to be established through Frisson Digital, Inc.** The `Billing Entity` column records what each account bills to *today*, which is a different question. Accounts predating the Frisson structure may still sit on a personal card. Those read `Unconfirmed` rather than being assumed.

## Schema note (2026-08-09)

Four columns added: `Billing Entity`, `Account Standing`, `Cost / Balance`, `Blocks Alpha`. Before this the format had nowhere to record an unpaid or exhausted account, which is why a $50 LiveKit balance and exhausted Runway credits both read as plain "Active."

## Services

| Service | Category | Purpose | Billing Entity | Account Standing | Cost / Balance | Blocks Alpha | Account / Org ID | Console URL | Subscription / Tier | Renewal | Credential Location | Status | Last Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub - studioyou-fy-agent | Other | Source code, CLAUDE.md, handoffs/ | Free / no billing | Free tier | $0 | no | github.com/supercreativepeople | https://github.com/supercreativepeople/studioyou-fy-agent | free | n/a | git credential helper (osxkeychain, de-tokenized 2026-08-07) | Active | 2026-08-07 |
| LiveKit Cloud | Hosting/Realtime | Voice/video agent runtime, FutureYou conversation rooms | Unconfirmed | **Balance due** | **$50 outstanding, unpaid** | **YES** | studioyou-futureyou-avatar-749nqz32.livekit.cloud, Agent ID CA_Mnhkjj3mUr7T | cloud.livekit.io | unconfirmed tier | n/a | LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET in .env | Active | 2026-08-09 |
| Runway | AI/API | Live avatar video rendering. Replaced Tavus as of Session AA | Unconfirmed | **Credits exhausted** | **needs top-up, amount TBD** | **YES** | RUNWAY_AVATAR_ID | runwayml.com | unconfirmed | n/a | RUNWAYML_API_SECRET / RUNWAY_AVATAR_ID in .env | Active | 2026-08-09 |
| Deepgram | AI/API | Speech-to-text (nova-3) for the FY voice agent | Unconfirmed | Unconfirmed | unconfirmed | unknown | - | deepgram.com | unconfirmed | n/a | **DEEPGRAM_API_KEY in .env (own key)** | Needs Verification | 2026-08-09 (corrected) |
| Cartesia | AI/API | Text-to-speech (sonic) for the FY voice agent | Unconfirmed | Unconfirmed | unconfirmed | unknown | - | cartesia.ai | unconfirmed | n/a | **CARTESIA_API_KEY in .env (own key)**, plus CARTESIA_PRONUNCIATION_DICT_ID, CARTESIA_TTS_SPEED | Needs Verification | 2026-08-09 (corrected) |
| Anthropic API (shared) | AI/API | Claude, agent conversation logic | Unconfirmed | Unconfirmed | see studioyou-backend/SERVICES.md | no | - | platform.claude.com | pay-as-you-go | n/a | ANTHROPIC_API_KEY in .env | Active | 2026-08-09 |
| Tavus | AI/API | **Deprecated.** Former avatar provider | Unconfirmed | Unconfirmed | unconfirmed | no | tavusapi.com | tavusapi.com | unconfirmed | n/a | TAVUS_API_KEY / TAVUS_LIVEKIT_PERSONA_ID / TAVUS_REPLICA_ID still in .env, unused here | Deprecated | 2026-08-09 |

## Correction logged 2026-08-09

The previous version of this file, and this repo's `CLAUDE.md`, both stated: "STT/TTS via LiveKit Inference (Deepgram nova-3 / Cartesia sonic), **no separate keys needed beyond the LiveKit credentials**."

That is wrong. `.env` in this repo contains standalone `DEEPGRAM_API_KEY` and `CARTESIA_API_KEY` entries. Both are therefore separately billed accounts that the tracker could not see, with unknown standing and unknown billing owner. They are now listed as their own rows above.

## Both alpha blockers live in this repo

The two accounts currently preventing the live IDEATE retest, and therefore alpha close, are both owned here:

1. **LiveKit, $50 due.** Without it the agent cannot hold a conversation room.
2. **Runway, credits exhausted.** Without it the avatar cannot render.

Per Lee (2026-08-09) the avatar feature itself is confirmed working. Neither of these is a technical failure; both are funding gaps.

## Open items

- [ ] Settle the LiveKit balance and top up Runway. Until both are done, no live FY session can run.
- [ ] Confirm Deepgram and Cartesia account standing and billing owner. Either could be a third hidden blocker.
- [ ] Billing entity audit: confirm which of these accounts bill to Frisson Digital, Inc. versus a personal card.
- [ ] Remove the unused `TAVUS_*` entries from `.env` once the backend's Tavus code paths are stripped.
- [ ] Fold the FY Agent history currently living in `studioyou-backend/CLAUDE.md` into this repo's own `handoffs/` over time.

Note: `.env` in this repo is properly gitignored and was confirmed not tracked in git history as of 2026-08-07.
