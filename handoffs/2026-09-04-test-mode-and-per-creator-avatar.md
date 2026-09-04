# Handoff: studioyou-fy-agent

Date: 2026-09-04 (session 4)
Session: Runway credit-drain fix (test_mode), Cartesia voice docstring drift, and per-creator avatar resolution.

Full architecture context lives in `studioyou-backend/handoffs/2026-09-04-test-mode-and-custom-avatar-groundwork.md` and in the Claude Project doc `claude/FutureYou_CustomAvatar_Architecture.md`. This handoff covers the agent side only.

## What Was Done

**test_mode gate added.** The agent was starting the Runway avatar eagerly on every job, before any user interaction, so every test session, page reload, and error recovery spent credits immediately. Runway bills 2 credits up front plus 2 per 6 seconds of active session, so the charge lands whether or not anyone speaks. This is why Lee had been disabling the avatar by hand during testing.

Lazy start was considered and rejected: `RoomOutputOptions(audio_enabled=False)` must be set at `session.start()` and cannot be flipped afterward, so the decision has to be made before the session starts.

The gate reads `formation_context["test_mode"]`. When true the agent skips `start_avatar()` and uses `RoomOutputOptions()` (Cartesia audio only). Conversation is fully functional with zero Runway spend.

**Cartesia voice docstring corrected.** The Session AD docstring claimed a switch to sonic-3.5 and the Jameson voice (`a5136bf9-224c-4d76-b823-52bd5efcffcc`) that was never made in code. Deployed code was, and remains, sonic-3 with Corey (`630ed21c-2c5c-41cf-9d82-10a7fd668370`). CLAUDE.md Live State was correct the whole time; the docstring was the only wrong artifact. Lee elected to keep Corey on sonic-3. The false claim was removed and the active voice recorded inline. Comment only, no behavior change.

**Per-creator avatar resolution.** The agent now resolves which avatar to use per session rather than always using the single env var. The module constant was renamed `RUNWAY_DEFAULT_AVATAR_ID` to make its fallback role explicit, and a local `avatar_id` is resolved once, immediately after `formation_context` is parsed:

```python
custom_avatar_id = formation_context.get("runway_avatar_id")
avatar_id = custom_avatar_id or RUNWAY_DEFAULT_AVATAR_ID
```

Everything downstream (open, close, rotation, the eager-start gate) now uses `avatar_id`. The only surviving references to the bare `RUNWAY_AVATAR_ID` name are the env lookup itself and the operator-facing warning log, both intentional.

Backward compatible. With no `creator_avatars` rows in Supabase, behavior is identical to before.

## What Was Found

**`lk agent deploy` works and preserves the agent ID.** CLAUDE.md Locked Decisions claimed `lk agent update` does not rebuild and that only `lk agent delete && lk agent create` produces a fresh image, with a new agent ID each time. That is no longer accurate. `lk agent deploy` rebuilt and shipped twice this session (16:36Z and 17:43:21Z), preserving agent ID `CA_Mnhkjj3mUr7T` and producing a new version string on each deploy. The delete and recreate dance, and the accompanying requirement to update the agent ID in CLAUDE.md after every deploy, are both retired. Corrected in the CLAUDE.md rebuild this close.

**The Runway avatar's `personality` and `startScript` are inert.** Per LiveKit's Runway integration docs, "LiveKit TTS settings will supersede selected voices and personalities configured for the Runway character." Cartesia generates speech and Runway only renders lip synced video. The personality text and opening script configured on The DUDE in the Runway dashboard are never read. Claude's system prompt, built in `prompts.py`, is the actual brain. Anyone editing The DUDE's personality in the Runway dashboard expecting a behavior change will see nothing happen.

This also means a Runway cloned voice would be silently ignored on this path, which is why voice cloning for custom avatars is routed to Cartesia instead.

## Files Changed

| File | Change | Commit |
|---|---|---|
| `agent.py` | `test_mode` gate before eager avatar start | `c998625` |
| `agent.py` | Session AD docstring corrected: removed false sonic-3.5 / Jameson claim, recorded active voice | `ee22229` |
| `agent.py` | Per-creator avatar resolution, `RUNWAY_DEFAULT_AVATAR_ID` rename | `a0c9ccf` |
| `SESSION_LOG.md` | New this close | this close |
| `CLAUDE.md` | Rebuilt: deploy method correction, avatar resolution, new Live State | this close |

## Git State at Close

HEAD `a0c9ccf` before this close's documentation commit. Clean and in sync with `origin/main`. Deployed: agent `CA_Mnhkjj3mUr7T`, version `Fqxg6JLvSBb8`, region us-east, 2026-09-04T17:43:21Z.

## Open Items and Carry-Forward

- TAVUS_* entries remain in `.env`. Backend code paths were stripped in `5172736`; this `.env` cleanup is the remaining half. Local file only, never in git.
- When the custom avatar pipeline ships, no further agent change is expected. The agent already reads `runway_avatar_id` from `formation_context`. `runway_voice_id` is currently injected by the backend but not yet consumed by the agent, since voice cloning will run through Cartesia rather than Runway. Wire it into the Cartesia TTS constructor when cloned voices exist.
- Avatar rotation (`AVATAR_ROTATION_SECONDS = 270`) is unchanged and still guards Runway's 5 minute platform cap. It now rotates whichever avatar was resolved for the session, custom or default, with no change needed.

## Next Session Opens With

Test the `test_mode` path end to end as `nyclaabq@gmail.com` in studio.html. Confirm the agent logs `test_mode=True, skipping Runway avatar, no credits used`, that conversation runs normally on Cartesia audio, and that Runway credit balance does not move. The deployed agent version to look for is `Fqxg6JLvSBb8`.

---

## RESOLVED same session: Runway credits were 0, topped to 3,000

**Resolution (2026-09-04, live-verified via `GET /v1/organization`): balance is 3,000.**
Lee topped up Runway Dev ($30.00, 09/04/2026 11:25 AM, 3,000 credits) and **enabled
autobilling**, set to auto-recharge whenever credits fall below 500, with a Visa card
saved to the project. The silent-zero failure mode described below is now CLOSED for
the first time since it was first flagged in July. Live avatar rendering and custom
avatar provisioning are unblocked.

Lifetime spend on Runway Dev is now $99.00 for 10,500 credits, roughly $0.0094 per credit.

One correction this resolution surfaced: a Runway **Platform** balance of 684 credits
was briefly read as evidence that credits were fine. It is not. Dev and Platform are
separate accounts with separate wallets. Always verify Dev via the API, never by
reading the Platform UI. See Locked Decisions.

The original finding is preserved below for the record.

---

### Original finding: Runway credit balance is 0

Live-verified via `GET https://api.dev.runwayml.com/v1/organization`: `creditBalance: 0`.

SERVICES.md recorded 2,500 credits as of 2026-08-17 with zero usage since. Those
credits are now gone. This is the exact silent-zero failure mode SERVICES.md already
flagged as still live (autobilling off, no card saved), and it is almost certainly the
eager-avatar-start drain fixed in this session having consumed the balance: the agent
started a billed Runway session on every job, before any user interaction, and Runway
bills 2 credits up front plus 2 per 6 seconds of active session.

Impact:

- Any work requiring live avatar rendering is BLOCKED until Lee tops up.
- E2E testing is NOT blocked. The `test_mode` path shipped this session skips the
  Runway avatar entirely and runs on Cartesia audio, so `nyclaabq@gmail.com` can
  exercise a full FY conversation at zero credit cost. The fix shipped today is
  precisely what makes testing possible despite the zero balance.
- Custom avatar provisioning (`POST /v1/avatars`) will also need credits, so the
  avatar pipeline build can proceed but cannot be live-tested until top-up.

Recommendation carried forward from SERVICES.md and now urgent: enable autobilling
with a threshold, or set a spend cap, before the next top-up. This is the second time
the balance has reached zero silently.

Account context verified same call: tier `maxMonthlyCreditSpend` 50000, and
`gen4_image_turbo` is present in the account's available models, confirming the
Gen-4 image path chosen for FutureYou portrait generation is actually available here.
