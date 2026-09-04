# CLAUDE.md - StudioYou FY Agent

> Project bible for this repo. Same 8 sections every session, same order. Carry-forwards live in `handoffs/`, not here. For platform-wide technical and deploy state, see `studioyou-backend/CLAUDE.md`. For strategy and positioning, see the StudioYou Project HQ in Notion.

**Changelog (most recent 3-5, older entries live in git history):**
- **2026-09-04 (session 4):** `test_mode` gate added so test sessions skip the Runway avatar entirely (eager avatar start was spending credits on every job before any user interaction). Per-creator avatar resolution added: `formation_context["runway_avatar_id"]` with fallback to the shared default; module constant renamed `RUNWAY_DEFAULT_AVATAR_ID`. Session AD docstring drift corrected (claimed a sonic-3.5/Jameson switch that was never made). **Three corrections to prior documentation: `lk agent deploy` preserves the agent ID (the `delete && create` procedure is retired), STT is nova-2 not nova-3, and TTS is sonic-3 with Corey not "sonic".** Commits `c998625`, `ee22229`, `a0c9ccf`.
- **2026-08-15:** Runway topped up. LiveKit was never in arrears (it is a current $50/mo Ship-plan subscription, corrected 2026-08-09). Both prior alpha blockers clear.
- **2026-08-09:** Corrected a false claim that STT/TTS needed no separate keys. `.env` holds standalone `DEEPGRAM_API_KEY` and `CARTESIA_API_KEY`; both are separately billed accounts.
- **2026-08-07:** dev-session-protocol bootstrap. `CLAUDE.md`, `handoffs/`, `SERVICES.md`, `tools/check_repo_status.sh`, `.dockerignore` and `livekit.toml` added.

---

## 1. What This Is

The LiveKit voice/video agent process for StudioYou's FutureYou (FY) conversational avatar. Runs separately from `studioyou-backend`: this process owns the live conversation room and avatar rendering, the backend owns the REST API and data. The backend passes everything the agent needs for a session as JSON in the job metadata, parsed into `formation_context`.

## 2. Repos & Access

| Repo | Local Mac Path | GitHub |
|---|---|---|
| studioyou-fy-agent | /Users/supercreativepeople/Projects/studioyou-fy-agent | github.com/supercreativepeople/studioyou-fy-agent |

Private. Credentials via macOS Keychain (`osxkeychain`). Git and `lk` CLI operations run through Desktop Commander, never `device_bash` (no network access in that sandbox).

`.env` is gitignored and confirmed not tracked in git history. It holds `RUNWAYML_API_SECRET`, `RUNWAY_AVATAR_ID`, `DEEPGRAM_API_KEY`, `CARTESIA_API_KEY`, `ANTHROPIC_API_KEY`, and LiveKit credentials. Pointers only in this file, never values.

## 3. Tech Stack & Architecture

**Framework:** livekit-agents 1.6.0. `AgentSession` with `RoomOptions`; entrypoint in `agent.py`, prompt construction in `prompts.py`.

**Model stack (verified against code 2026-09-04):**

| Layer | Value |
|---|---|
| LLM | `claude-sonnet-4-6` via `anthropic.LLM` |
| STT | Deepgram `nova-2` |
| TTS | Cartesia `sonic-3`, voice Corey (`630ed21c-2c5c-41cf-9d82-10a7fd668370`), en-US male |
| Avatar | Runway Characters via `runway.AvatarSession` |

`CARTESIA_PRONUNCIATION_DICT_ID` and `CARTESIA_TTS_SPEED` are env-driven so they can be tuned by ear without a code change. Both only take effect on sonic-3.

**Data channels:** `fy_chat` (inbound text), `fy_directive` (outbound replies, section recommendations, vault captures, visual generation), `fy_avatar_control` (avatar on/off toggle), `fy_say_verbatim` (direct TTS bypassing the LLM, for scripted lines).

**Function tools:** `recommend_section`, `capture_vault_entry`, `generate_visual`.

**Avatar lifecycle.** Runway bills 2 credits up front plus 2 per 6 seconds of ACTIVE avatar-session time, not per utterance, so muting playback client-side does nothing. Closing the `AvatarSession` is the only way to stop the charge. Runway also hard-caps sessions at 5 minutes platform-side with no renew/extend call in the plugin, so `AVATAR_ROTATION_SECONDS = 270` proactively closes and reopens a fresh session 30 seconds before the cap. Rotation is cancelled cleanly on manual toggle-off.

When the avatar is active the agent sets `RoomOutputOptions(audio_enabled=False)` because Runway streams audio through its own video track. This must be decided before `session.start()` and cannot be changed after init, which is why avatar usage is resolved up front rather than lazily.

## 4. Services

Full registry in `SERVICES.md`. Credentials are pointers only.

| Service | Purpose | Credential Location |
|---|---|---|
| LiveKit | Agent host, voice rooms | `.env` (Ship plan, $50/mo, current) |
| Runway | Avatar rendering (Characters) | `.env` (`RUNWAYML_API_SECRET`, `RUNWAY_AVATAR_ID`) |
| Cartesia | TTS | `.env` (`CARTESIA_API_KEY`, separately billed) |
| Deepgram | STT | `.env` (`DEEPGRAM_API_KEY`, separately billed) |
| Anthropic | Claude API | `.env` (`ANTHROPIC_API_KEY`) |

## 5. How to Deploy

Code edit → `git commit && git push` (for record) → `lk agent deploy` from the repo root.

`lk agent deploy` rebuilds the Docker image and **preserves the agent ID**, issuing a new version string each deploy. The build takes a few minutes, so run it detached and poll rather than blocking on a short tool timeout:

```bash
cd /Users/supercreativepeople/Projects/studioyou-fy-agent
nohup lk agent deploy > /tmp/lk_deploy.log 2>&1 &
# poll: tail /tmp/lk_deploy.log   then confirm: lk agent list
```

Confirm with `lk agent list` and update the version in Live State below.

## 6. Live State

| Component | Current Value |
|---|---|
| Agent ID | `CA_Mnhkjj3mUr7T` (region us-east). Stable across deploys. |
| Agent version | `Fqxg6JLvSBb8`, deployed 2026-09-04T17:43:21Z |
| Repo HEAD | `a0c9ccf` (before session-close documentation commit) |
| Default avatar | "The DUDE" `d44bf1d0-c297-4e26-839a-93099a485ca5` via `RUNWAY_AVATAR_ID` |
| Custom avatars | Agent-side complete. Reads `formation_context["runway_avatar_id"]`, falls back to default. Backend injects it from `public.creator_avatars`. Creation pipeline unbuilt. |
| Test mode | `formation_context["test_mode"]` skips the avatar entirely. `nyclaabq@gmail.com` is the E2E test account, auto-detected backend-side. |
| Runway credits (Dev) | **3,000 as of 2026-09-04 (live-verified via `GET /v1/organization`).** Autobilling ENABLED, recharges below 500, Visa saved. Live avatar rendering unblocked. |
| Avatar rotation | 270s, guards Runway's 300s hard cap |
| Known cleanup | `TAVUS_*` entries still in `.env`. Backend paths stripped in `5172736`; this is the remaining half. |

## 7. Locked Decisions

- **`lk agent deploy` is the deploy command (corrected 2026-09-04).** It rebuilds and preserves the agent ID. Verified twice on 2026-09-04 (16:36Z, 17:43:21Z) with `CA_Mnhkjj3mUr7T` unchanged across both. The prior guidance that only `delete && create` rebuilds, and that the agent ID changes every deploy, is obsolete. Do not delete the agent to ship a change.
- **Runway bills on ACTIVE session time, not per utterance.** Closing the `AvatarSession` is the only way to stop the charge. Never start an avatar speculatively.
- **Runway is TWO separate accounts.** `RUNWAYML_API_SECRET` in this repo's `.env` authenticates against Runway **Dev** (`api.dev.runwayml.com`), which is the balance the avatar spends. Runway **Platform** (`runway.com`) is a separate account with its own wallet, and a healthy Platform balance does NOT unblock the avatar. Verify with `GET https://api.dev.runwayml.com/v1/organization`, never the Platform UI.
- **Avatar usage must be decided before `session.start()`.** `RoomOutputOptions(audio_enabled=False)` cannot be flipped after init. This is why lazy avatar start was evaluated and rejected.
- **Runway avatar `personality` and `startScript` are INERT.** Per LiveKit's Runway docs, "LiveKit TTS settings will supersede selected voices and personalities configured for the Runway character." Cartesia generates the speech; Runway only renders lip-synced video. `prompts.py` is the actual brain. Editing The DUDE's personality in the Runway dashboard changes nothing, and a Runway-cloned voice would likewise be ignored.
- **STT is nova-2 and TTS is sonic-3 with Corey.** Verified against code 2026-09-04. Earlier docs claiming nova-3, or a sonic-3.5/Jameson switch, were wrong. Trust the code over any doc claim here.
- **`.env` is local-only.** Never committed, never passed through chat, never echoed. Runway/Cartesia/Deepgram/Anthropic keys all live there.
- **Tavus is deprecated.** Replaced by Runway Characters.

## 8. Key Contacts

| Person | Role | Relevance |
|---|---|---|
| Carson | LiveKit | AIEWF contact. Shared voice agent demos/docs. Unreplied. |
| Alberto | Reactor CEO | FY avatar/video partner ($59M funded) |
| Ahmed | Reactor GTM | Commercial lead. Rescheduled Jul 2 pre-talk, no follow-up since. |

Runway partnership pursuit is active. Note the standing rule from `studioyou-backend/CLAUDE.md`: partnership value stays strictly downstream of the technical call and never drives tool selection.
