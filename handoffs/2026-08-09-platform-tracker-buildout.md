# Session: platform / partner / subscription tracker build-out — 2026-08-09

Cross-repo session. Full record in `studioyou-backend/handoffs/2026-08-09-platform-tracker-buildout.md`. This file covers what changed here.

## Both alpha blockers live in this repo

- **LiveKit: $50 balance due, unpaid.** Without it the agent cannot hold a conversation room.
- **Runway: credits exhausted.** Without it the avatar cannot render.

Per Lee, the avatar feature itself is confirmed working. Neither is a technical failure; both are funding gaps. Together they mean no live FY session can run, so the live IDEATE retest, the gate on alpha close, cannot be attempted. Both are now recorded in `SERVICES.md` with `Account Standing` and `Blocks Alpha` set, and mirrored into the Notion registry.

## Documented error corrected

`CLAUDE.md` and `SERVICES.md` in this repo both stated that STT/TTS run "via LiveKit Inference, no separate keys needed beyond the LiveKit credentials."

That is wrong. `.env` contains standalone `DEEPGRAM_API_KEY` and `CARTESIA_API_KEY`. Both are separately billed accounts with unknown standing that the tracker could not see. They now have their own rows. Either could be a further hidden blocker.

## Schema and corporate structure

`SERVICES.md` gained `Billing Entity`, `Account Standing`, `Cost / Balance`, and `Blocks Alpha` columns, matching the other three repos and the Notion registry. Before this there was nowhere to record an unpaid or exhausted account, which is exactly why a $50 arrears and exhausted credits both read as "Active."

Corporate structure recorded: **Frisson Digital, Inc. is the parent company owning both StudioYou and SCREENBot**, superseding the per-product newco plan. Every paid resource is currently funded on Lee's personal cards; target state is every billing instance through Frisson. StudioYou and SCREENBot remain **independent products** under a common parent.

## Open items

- [ ] Settle the LiveKit balance and top up Runway. Nothing else here can proceed first.
- [ ] Confirm Deepgram and Cartesia account standing and billing owner.
- [ ] Move billing from Lee's personal cards to a Frisson instrument.
- [ ] Remove unused `TAVUS_*` entries from `.env` once the backend's Tavus code paths are stripped.
- [ ] Carried: fold FY Agent history out of `studioyou-backend/CLAUDE.md` into this repo's `handoffs/`.
