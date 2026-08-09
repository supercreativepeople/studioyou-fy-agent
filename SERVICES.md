# SERVICES.md - StudioYou FY Agent

Every external platform/service this project depends on. Update at session close whenever something changes. Credentials are NEVER stored here, pointer only. Mirrored into the cross-project Notion Platform & Service Registry (`https://app.notion.com/p/dd60c5c5ccda496eb10d58f8db0bc8b6`) at session close per the `dev-session-protocol` skill.

## Corporate / billing structure (recorded 2026-08-09)

**Frisson Digital, Inc. is the parent company and owns both StudioYou and SCREENBot.** This supersedes the earlier per-product newco plan (StudioYou Inc., Delaware C-corp, with SCP Inc. as venture studio) still described in `studioyou-backend/CLAUDE.md`. A single parent owning both products aligns with incubator programs, Anthropic's programs, and fundraising opportunities.

**Confirmed by Lee 2026-08-09:** every paid resource is personally funded by Lee on personal cards. No platform account bills to a company instrument today, which is why `Billing Entity` reads `Lee (personal)` throughout. SCP Inc. owns nothing and has no IP assigned to it. StudioYou and SCREENBot each have executed IP assignment documentation to Frisson Digital, Inc.; they are the two assigned products. StudioYou and SCREENBot remain **independent products** under a common parent, so shared tooling must not assume a shared codebase or runtime.

**Gap:** Frisson owns the IP, Lee's personal cards fund the infrastructure it runs on. That mismatch is the kind of thing raised in incubator and fund diligence. Counsel and accountant question, flagged here, not advice.

**Target state:** every billing instance established through Frisson Digital, Inc.

## Schema note (2026-08-09)

Four columns added: `Billing Entity`, `Account Standing`, `Cost / Balance`, `Blocks Alpha`. Before this the format had nowhere to record an unpaid or exhausted account, which is why a $50 LiveKit balance and exhausted Runway credits both read as plain "Active."

## Services

| Service | Category | Purpose | Billing Entity | Account Standing | Cost / Balance | Blocks Alpha | Account / Org ID | Console URL | Subscription / Tier | Renewal | Credential Location | Status | Last Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub - studioyou-fy-agent | Other | Source code, CLAUDE.md, handoffs/ | Free / no billing | Free tier | $0 | no | github.com/supercreativepeople | https://github.com/supercreativepeople/studioyou-fy-agent | free | n/a | git credential helper (osxkeychain, de-tokenized 2026-08-07) | Active | 2026-08-07 |
| LiveKit Cloud | Hosting/Realtime | Voice/video agent runtime, FutureYou conversation rooms | Lee (personal) | **Balance due** | **$50 owed, account still LIVE** | no | studioyou-futureyou-avatar-749nqz32.livekit.cloud, Agent ID CA_Mnhkjj3mUr7T | cloud.livekit.io | unconfirmed tier | n/a | LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET in .env | Active | 2026-08-09 |
| Runway | AI/API | Live avatar video rendering. Replaced Tavus as of Session AA | Lee (personal) | **Credits exhausted** | **needs top-up, amount TBD** | **YES** | RUNWAY_AVATAR_ID | runwayml.com | unconfirmed | n/a | RUNWAYML_API_SECRET / RUNWAY_AVATAR_ID in .env | Active | 2026-08-09 |
| Deepgram | AI/API | Speech-to-text (nova-3) for the FY voice agent | Lee (personal) | Unconfirmed | unconfirmed | unknown | - | deepgram.com | unconfirmed | n/a | **DEEPGRAM_API_KEY in .env (own key)** | Needs Verification | 2026-08-09 (corrected) |
| Cartesia | AI/API | Text-to-speech (sonic) for the FY voice agent | Lee (personal) | Unconfirmed | unconfirmed | unknown | - | cartesia.ai | unconfirmed | n/a | **CARTESIA_API_KEY in .env (own key)**, plus CARTESIA_PRONUNCIATION_DICT_ID, CARTESIA_TTS_SPEED | Needs Verification | 2026-08-09 (corrected) |
| Anthropic API (shared) | AI/API | Claude, agent conversation logic | Lee (personal) | Unconfirmed | see studioyou-backend/SERVICES.md | no | - | platform.claude.com | pay-as-you-go | n/a | ANTHROPIC_API_KEY in .env | Active | 2026-08-09 |
| Tavus | AI/API | **Deprecated.** Former avatar provider | Lee (personal) | Unconfirmed | unconfirmed | no | tavusapi.com | tavusapi.com | unconfirmed | n/a | TAVUS_API_KEY / TAVUS_LIVEKIT_PERSONA_ID / TAVUS_REPLICA_ID still in .env, unused here | Deprecated | 2026-08-09 |

## Correction logged 2026-08-09

The previous version of this file, and this repo's `CLAUDE.md`, both stated: "STT/TTS via LiveKit Inference (Deepgram nova-3 / Cartesia sonic), **no separate keys needed beyond the LiveKit credentials**."

That is wrong. `.env` in this repo contains standalone `DEEPGRAM_API_KEY` and `CARTESIA_API_KEY` entries. Both are therefore separately billed accounts that the tracker could not see, with unknown standing and unknown billing owner. They are now listed as their own rows above.

## One hard blocker lives in this repo (corrected 2026-08-09)

**Runway, credits exhausted.** Without it the avatar cannot render, so no live FY session can run. This is the sole hard blocker on the live IDEATE retest and therefore on alpha close.

**LiveKit, $50 owed, but the account is still live.** An earlier version of this file listed LiveKit as a second blocker. Lee confirmed the account has not been suspended, so the balance is owed rather than blocking. LiveKit is also first on his AIEWF follow-up list and may yield a partnership track that removes the $50 entirely; if not, he renews 2026-08-10.

Per Lee the avatar feature itself is confirmed working. This is a funding gap, not a technical failure.

## Open items

- [ ] Settle the LiveKit balance and top up Runway. Until both are done, no live FY session can run.
- [ ] Confirm Deepgram and Cartesia account standing and billing owner. Either could be a third hidden blocker.
- [ ] Billing entity audit: confirm which of these accounts bill to Frisson Digital, Inc. versus a personal card.
- [ ] Remove the unused `TAVUS_*` entries from `.env` once the backend's Tavus code paths are stripped.
- [ ] Fold the FY Agent history currently living in `studioyou-backend/CLAUDE.md` into this repo's own `handoffs/` over time.

Note: `.env` in this repo is properly gitignored and was confirmed not tracked in git history as of 2026-08-07.

## Asset class correction (2026-08-09)

`Lee (personal)` in the Billing Entity column is **not** a defect on every row. Lee operates as an independent builder; his personal accounts and cards fund his own activities and have never been commingled with SCP Inc. or any other company. Personal tooling on a personal card is correct and stays that way.

The real finding is **asset control**: which accounts a Frisson-owned product cannot operate without, while being held in Lee's personal name. The IP assignment moved StudioYou and SCREENBot to Frisson; it did not move the domain registrations, platform accounts, or API keys those products run on. That is a completeness gap in the assignment, not a hygiene failure.

Separately: every vendor account was signed up via `supercreativepeople@gmail.com` with the company name listed as **"SuperCreativePeople"** (name only, no EIN, no entity linkage). SCP Inc. is the one entity deliberately excluded from every program application, so having it named on the infrastructure is a needless inconsistency. **Decision: strip the SCP name now; do not replace with Frisson until Frisson has a payment instrument.** Do not touch GCP billing account `019309-BEB782-398472` while the Google for Startups application is under review.

Full analysis, the company-dependent asset list, and the open items live in `studioyou-backend/SERVICES.md`.
