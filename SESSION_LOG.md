# Session Log — 2026-09-04

Session type: repo
Repo: studioyou-fy-agent (worked alongside studioyou-backend, which holds the primary log for this session)
Tokens at open: 14,982,269 (session opened against studioyou-backend)
Tasks in scope: Runway credit-drain audit, Cartesia voice drift, custom FutureYou avatar groundwork

Note: this file was created at session close. The session's primary log lives in
`studioyou-backend/SESSION_LOG.md`; this file records the agent-side entries so the
repo carries its own record. Continuous logging lapsed across a compaction boundary
mid-session and entries below were reconstructed from git history and live tool
results rather than context.

---

[FOUND] — agent.py: Runway credit drain root cause is EAGER avatar start.
  `if RUNWAY_AVATAR_ID: await start_avatar()` runs on every job before any user
  interaction. Runway bills 2 credits up front + 2 per 6s of ACTIVE session, so every
  test session, reload, and error recovery spends credits regardless of whether anyone
  speaks. This is why Lee was disabling the avatar manually during testing.

[DECISION] — lazy start rejected. RoomOutputOptions(audio_enabled=False) must be set AT
  session.start() and cannot be flipped after init, so whether the avatar is used has
  to be known before the session starts.

[FIX] — agent.py: test_mode gate added before the eager-start block. Skips
  start_avatar() and uses plain RoomOutputOptions() (Cartesia audio only). Full
  conversation, zero Runway spend. Commit c998625. Deployed 16:36Z.

[FOUND] — agent.py Session AD docstring claimed "Switched model sonic-3 -> sonic-3.5
  and voice Parker -> Jameson (a5136bf9-224c-4d76-b823-52bd5efcffcc)". Deployed code is
  and always was sonic-3 + Corey (630ed21c-2c5c-41cf-9d82-10a7fd668370). CLAUDE.md Live
  State was CORRECT; the docstring was the sole wrong artifact.

[DECISION] — Lee: keep Corey on sonic-3, revisit later if needed.

[FIX] — agent.py: removed the false sonic-3.5/Jameson claim, recorded active voice
  inline. Comment only, no behavior change. Commit ee22229.

[FOUND] — Runway dev API probed live (docs contradict themselves). POST /v1/avatars is
  real: requires name, referenceImage, personality, voice (object, discriminated on
  .type). NO training step, status returns READY immediately. referenceImage is fetched
  SERVER-SIDE from a URL. Runway also does native voice cloning via
  POST /v1/voices {name, from:{type:"audio"}}.

[FOUND] — account holds one avatar: "The DUDE" d44bf1d0-c297-4e26-839a-93099a485ca5,
  matching RUNWAY_AVATAR_ID in .env. voice = {type:"runway-live-preset", presetId:"zach"}.

[FOUND] — BLOCKER on Runway voice consolidation. LiveKit docs: "LiveKit TTS settings
  will supersede selected voices and personalities configured for the Runway character."
  Cartesia generates speech; Runway only renders lip-synced video. A Runway-cloned voice
  would be silently ignored on this path.

[FOUND] — consequence: The DUDE's `personality` and `startScript` set in the Runway
  dashboard are INERT. prompts.py builds the actual brain. Editing personality in the
  Runway dashboard produces no behavior change.

[FIX] — agent.py: per-creator avatar resolution. Module constant renamed
  RUNWAY_DEFAULT_AVATAR_ID; local avatar_id resolved from
  formation_context["runway_avatar_id"] with fallback. All downstream open/close/
  rotation/eager-start now use avatar_id. Only surviving bare RUNWAY_AVATAR_ID refs are
  the env lookup and the operator warning log, both intentional. Backward compatible.
  Commit a0c9ccf.

[DEPLOY] — lk agent deploy completed 17:43:21Z. Agent CA_Mnhkjj3mUr7T preserved,
  version Fqxg6JLvSBb8, region us-east.

[FOUND] — CLAUDE.md Locked Decision "lk agent update does not rebuild; only delete &&
  create produces a fresh image + new agent ID" is VERIFIED FALSE. `lk agent deploy`
  rebuilt and shipped twice this session (16:36Z, 17:43:21Z) while PRESERVING agent ID
  CA_Mnhkjj3mUr7T, new version string each time. Delete/create dance retired. Corrected
  in CLAUDE.md this close.

[CHECKPOINT] — tokens remaining: ~14,959,000
