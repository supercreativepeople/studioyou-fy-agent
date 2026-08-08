# CLAUDE.md - StudioYou FY Agent

**Last updated:** 2026-08-07 (dev-session-protocol bootstrap, closed same day)
**Next session opens with:** no carried-forward task list — pick up wherever the last real work session left off (this repo had no CLAUDE.md before today, so check `studioyou-backend/CLAUDE.md`'s FY Agent Reference section for the fuller picture until this file grows its own).

## What this is

The LiveKit voice/video agent process for StudioYou's "FutureYou" (FY) conversational avatar. Runs separately from `studioyou-backend` — this process owns the live conversation room and avatar rendering; the backend owns the REST API and data.

## Current state (as of 2026-08-07)

- Agent ID `CA_Mnhkjj3mUr7T`, running on LiveKit Cloud (us-east).
- Avatar rendering provider is **Runway** (`RUNWAYML_API_SECRET`, `RUNWAY_AVATAR_ID`), replacing Tavus as of an earlier session. Tavus env vars may still be referenced elsewhere as legacy/unused — see `studioyou-backend/CLAUDE.md` for that history.
- STT/TTS via LiveKit Inference (Deepgram nova-3 / Cartesia sonic), no separate keys needed beyond the LiveKit credentials.
- `.env` is properly gitignored and confirmed not tracked in git history.

## Protocol structure (added 2026-08-07)

This repo did not have `CLAUDE.md`, `handoffs/`, `SERVICES.md`, or `tools/check_repo_status.sh` before today. All four were added per the `dev-session-protocol` skill. This file is intentionally minimal — the deeper build history lives in `studioyou-backend/CLAUDE.md`'s "LiveKit / FY Agent Reference" section until this repo accumulates its own session history in `handoffs/`.

See `SERVICES.md` for what this repo depends on externally.

## Open items

- [ ] Fold the FY Agent history currently living in `studioyou-backend/CLAUDE.md` into this repo's own `handoffs/` over time, so this repo's history isn't split across two files.
- [x] `.dockerignore` and `livekit.toml` — committed 2026-08-07 per Lee's decision.

Repo is clean and fully pushed to GitHub as of session close (2026-08-07).
