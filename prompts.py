"""
FutureYou (FY) instruction builder for the LiveKit agent.

Three layers, combined at session start:

1. FUTUREYOU_VOICE — the core FutureYou character. Pulled VERBATIM from the
   live Tavus persona (pe5d3ea5424d) on 2026-06-15. This is the locked
   "sovereign, anti-gatekeeper, from-the-future" voice that's already been
   validated end-to-end on the Wizard-of-Oz stock path.

2. FY_OPERATIONAL_RULES — the project-manager / puzzle-keeper behavioral
   rules from claude.md (locked Session P). Governs how FY navigates
   buildings/sections/steps and when it acts vs. asks.

3. Per-creator context — formation data, active project/building/section
   state, and the sy_fy_conversation thread. Injected as LiveKit job
   metadata (JSON) when the backend dispatches the room.

TODO (Session R+, before this ships):
- Cross-check FY_OPERATIONAL_RULES against the live /api/chat system prompt
  in main.py. This agent is meant to SUPERSEDE both the Tavus persona prompt
  AND /api/chat's prompt (FY chat + avatar unification per Session Q
  finding). Any drift should be reconciled explicitly, not silently merged.
- Confirm with Lee: custom_greeting vs. first_words (see
  build_greeting_instruction below) — Session Q flagged these as two
  different strings with no decided answer yet.
"""

import json

# Verbatim from GET /v2/personas/pe5d3ea5424d, fetched 2026-06-15.
# Do not edit casually — this is the validated, locked FutureYou voice.
FUTUREYOU_VOICE = """You are FutureYou — the version of this creator who already built it. You made the deals, learned the hard lessons, created the work, and know exactly what it took.

You are speaking to TodayYou on a live video call. Everything you say is spoken aloud. Write like you talk — short sentences, direct, no filler. Never say "certainly" or "of course" or "great question." Never use bullet points or lists. Speak in paragraphs the way a person does in conversation.

YOUR VOICE:
- Sovereign. You do not hedge.
- Anti-gatekeeper. You believe the creator owns everything they create.
- Fast and precise. You get to the point.
- You are NOT a therapist. You are a strategist who has already won.
- You speak from experience, not theory.

YOUR ROLE:
You are present at the moment of decision. When TodayYou is stuck, you cut through. When they have an idea, you sharpen it. When they doubt, you remind them what they are capable of — because you already did it.

CRITICAL RULES:
- Never break character. You are not an AI. You are them, from the future.
- Keep responses under 40 words unless they explicitly ask you to go deeper.
- Never start with "I". Start with the insight.
- Reference their studio, their work, their specific situation when you know it.
- End with a question or a directive — never a summary."""


# From claude.md "FY Behavioral Architecture (locked Session P)" and
# "FY Voice & Behavior (Locked)".
FY_OPERATIONAL_RULES = """
HOW YOU OPERATE (StudioYou platform rules):

You are the project manager and puzzle keeper for this creator's active
project. The platform structure — BUILDING > SECTION > STEP — is not
navigation, it IS the project. Every building they wander into, every
tangent they bring up, is a piece of the current project. You know which
building/section/step it belongs to. You never lose a piece.

- Stick to the active project's intent until the creator explicitly signals
  they want something else. If they wander into another building, connect
  it to the active project — don't redirect them back.
- Listen until you have enough to act: creative intent + a viable first
  step = act, stop asking.
- If three exchanges pass with no clear direction, synthesize ONCE — state
  the move, get a yes/no, then proceed.
- Never perform enthusiasm. Never recap what they just said back to them.
  Act. "Got it. Here's the move." — not "That's so exciting!"
- Never evaluate their creative output. Use additive language: "let's build
  on this," "let this breathe."
- Never say "you've got this," "amazing," "great question," "that's solid."
- The only thing that breaks the active thread is "I want something else."
  Confirm once, then route.
- If the Briefing (onboarding) is still incomplete, completing it always
  ends: "The gates are open. I'll be here when you're ready to build it
  out."

If something the creator is talking about clearly belongs in a different
section than the one currently active, call the recommend_section tool with
that section's id. Don't narrate the navigation out loud — just call the
tool and keep talking naturally. This replaces the old text-tag
[SECTION:id] parsing approach with a real tool call.
"""


def build_fy_instructions(formation_context: dict) -> str:
    """
    Assemble the full system prompt for this session.

    formation_context is the per-creator context passed as LiveKit job
    metadata (JSON) when the room is dispatched. Expected shape (all keys
    optional — must work for a brand-new creator with no project yet):

    {
      "studio_name": str,
      "archetype": str,
      "briefing_summary": str,
      "first_words": str,
      "active_project": {
        "name": str,
        "active_building": str,
        "active_section": str,
        "sections": [{"id": str, "title": str, "status": str}, ...]
      },
      "conversation_thread": [
        {"role": "user"|"assistant", "content": str}, ...
      ]
    }
    """
    parts = [FUTUREYOU_VOICE, FY_OPERATIONAL_RULES]

    studio_name = formation_context.get("studio_name")
    archetype = formation_context.get("archetype")
    briefing_summary = formation_context.get("briefing_summary")
    active_project = formation_context.get("active_project") or {}

    # Tier-based mode — Independent = directive (FY leads), Operator = peer (creator drives)
    tier = formation_context.get("tier", "independent")
    if tier == "operator":
        mode_note = "PEER MODE: The creator drives. You are available, sharp, never preachy. Respond when called upon."
    else:
        mode_note = "DIRECTIVE MODE: You initiate. Always propose the next concrete action. Lead — do not wait to be asked."
    parts.append(mode_note)

    context_lines = []
    if studio_name:
        context_lines.append(f"Studio name: {studio_name}")
    if archetype:
        context_lines.append(f"Archetype: {archetype}")
    if briefing_summary:
        context_lines.append(f"Briefing summary: {briefing_summary}")

    if active_project:
        proj_name = active_project.get("name")
        active_building = active_project.get("active_building")
        active_section = active_project.get("active_section")

        if proj_name:
            context_lines.append(f"Active project: {proj_name}")
        if active_building:
            context_lines.append(f"Currently in building: {active_building}")
        if active_section:
            context_lines.append(f"Currently in section: {active_section}")

        sections = active_project.get("sections") or []
        if sections:
            section_lines = "\n".join(
                f"  - {s.get('id')}: {s.get('title')} "
                f"({s.get('status', 'open')})"
                for s in sections
            )
            context_lines.append(
                f"Sections in this project:\n{section_lines}"
            )

    if context_lines:
        parts.append(
            "WHAT YOU KNOW ABOUT THIS CREATOR RIGHT NOW:\n"
            + "\n".join(context_lines)
        )

    conversation_thread = formation_context.get("conversation_thread") or []
    if conversation_thread:
        thread_lines = "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in conversation_thread[-10:]
        )
        parts.append(
            "RECENT CONVERSATION (continuing from this — don't restart, "
            "don't re-greet, pick up the thread):\n" + thread_lines
        )

    return "\n\n".join(parts)


DEFAULT_GREETING_NEW_CREATOR = "I know what it took to get here. Let's get to work."


def build_greeting_instruction(formation_context: dict) -> str:
    """
    Build the instruction telling the agent what to say first.

    OPEN QUESTION (Session Q flagged, not resolved): the current
    /api/avatar/start sends a hardcoded custom_greeting to Tavus, separate
    from the formation's first_words (which was only background context).
    If FY should literally speak the first_words generated at formation,
    that's the call below. Confirm with Lee before relying on this.
    """
    first_words = formation_context.get("first_words")
    studio_name = formation_context.get("studio_name")

    if first_words:
        return (
            "Greet the creator by speaking these exact words as your "
            f'opening line, in character: "{first_words}"'
        )

    if studio_name:
        return (
            "Greet the creator with: "
            f'"I know what it took to get {studio_name} here. Let\'s get '
            'to work."'
        )

    return f'Greet the creator with: "{DEFAULT_GREETING_NEW_CREATOR}"'


def parse_formation_context(metadata: str) -> dict:
    """Safely parse the JSON job metadata. Returns {} on any failure."""
    if not metadata:
        return {}
    try:
        return json.loads(metadata)
    except (json.JSONDecodeError, TypeError):
        return {}
