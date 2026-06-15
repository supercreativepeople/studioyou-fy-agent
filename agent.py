"""
FutureYou LiveKit Agent — Session R scaffold.

Architecture (per Session Q finding):
  LiveKit Agent (this process) = the conversational brain. Claude
  (claude-sonnet-4-6) is the LLM. Tavus is used ONLY for avatar video
  rendering via livekit-plugins-tavus (transport_type: livekit,
  pipeline_mode: echo) — Tavus's own persona/Sparrow/Raven turn-taking
  system is NOT used here, it's replaced by this agent.

  This is the same agent for both surfaces:
    - FY avatar (video call, this agent + Tavus rendering)
    - FY chat (text-only — same agent, audio_enabled can stay off,
      tavus avatar can be omitted)
  That unification fixes the chat/avatar disconnect (Session Q Gap 2)
  and IS the FY conversation continuity item.

STATUS: scaffold only. NOT yet deployed or run against a live LiveKit
project. Things still needed before this works end-to-end:

  1. A new Tavus persona with pipeline_mode="echo" and
     layers.transport.transport_type="livekit". DONE — pb0277f1cfc1,
     created 2026-06-15. Set TAVUS_LIVEKIT_PERSONA_ID in .env.
  2. Backend (main.py) needs a new endpoint that creates a LiveKit room,
     generates an access token for the frontend, and dispatches this agent
     with job metadata (formation context + active project + conversation
     thread as JSON). Replaces /api/avatar/start's Tavus flow.
  3. Frontend FYAvatarSlot needs to become a LiveKit React client instead
     of <iframe src={Daily convUrl}> — fixes Session Q Gap 1.

STT/TTS: using LiveKit Inference (inference.STT / inference.TTS) —
authenticated via the existing LIVEKIT_API_KEY/SECRET, no separate provider
accounts or keys needed. Every LiveKit Cloud plan includes free monthly
inference credits.

Run locally once .env is filled in:
    python agent.py dev      # connect to LiveKit Cloud, local dev mode
    python agent.py start    # production worker
"""

import json
import logging
import os

from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
    inference,
)
from livekit.plugins import anthropic, silero, tavus
from dotenv import load_dotenv

from prompts import (
    build_fy_instructions,
    build_greeting_instruction,
    parse_formation_context,
)

load_dotenv()
logger = logging.getLogger("futureyou-agent")

# Raj — stock Wizard-of-Oz replica, validated end-to-end in Session Q.
STOCK_REPLICA_ID = os.environ.get("TAVUS_REPLICA_ID", "rf8f3aa4b33e")

# LiveKit-mode persona — pipeline_mode=echo, transport_type=livekit.
# Created 2026-06-15. Set TAVUS_LIVEKIT_PERSONA_ID=pb0277f1cfc1 in .env.
TAVUS_LIVEKIT_PERSONA_ID = os.environ.get("TAVUS_LIVEKIT_PERSONA_ID")


class FutureYouAgent(Agent):
    """
    FutureYou — same agent for chat and avatar surfaces.

    The recommend_section tool is the structured fix for the Session Q
    [SECTION:id] parsing bug: instead of string-matching FY's prose for
    navigation hints (which false-positived on substrings like "story"
    inside "storyboards"), FY calls this tool explicitly. The agent
    publishes the recommendation to the room's data channel; the frontend
    listens on topic "fy_directive" for the JSON payload.
    """

    def __init__(self, instructions: str, room) -> None:
        super().__init__(instructions=instructions)
        self._room = room

    @function_tool()
    async def recommend_section(
        self, context: RunContext, section_id: str, reason: str
    ) -> str:
        """Call this when the current topic clearly belongs in a different
        section of the active project than the one currently active.

        Args:
            section_id: The id of the section this belongs in, exactly as
                given in the "Sections in this project" list.
            reason: One short phrase for logging only — never spoken aloud.
        """
        payload = json.dumps(
            {"type": "fy_section_recommendation", "section_id": section_id}
        ).encode("utf-8")

        try:
            await self._room.local_participant.publish_data(
                payload, topic="fy_directive"
            )
        except Exception:
            logger.exception(
                "Failed to publish section recommendation for %s", section_id
            )

        logger.info(
            "FY recommended section=%s reason=%s", section_id, reason
        )
        return "noted"


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    formation_context = parse_formation_context(ctx.job.metadata)
    instructions = build_fy_instructions(formation_context)
    greeting_instruction = build_greeting_instruction(formation_context)

    agent = FutureYouAgent(instructions=instructions, room=ctx.room)

    session = AgentSession(
        llm=anthropic.LLM(model="claude-sonnet-4-6"),
        vad=ctx.proc.userdata["vad"],
        # LiveKit Inference — authenticated via LIVEKIT_API_KEY/SECRET.
        # No separate Deepgram/Cartesia accounts needed.
        # cartesia/sonic matches the TTS on the existing Tavus persona.
        stt=inference.STT(model="deepgram/nova-3"),
        tts=inference.TTS(model="cartesia/sonic"),
    )

    # Attach Tavus avatar rendering if configured. Falls back gracefully
    # to audio-only (text-chat-only surface) if not set.
    if TAVUS_LIVEKIT_PERSONA_ID:
        avatar = tavus.AvatarSession(
            replica_id=STOCK_REPLICA_ID,
            persona_id=TAVUS_LIVEKIT_PERSONA_ID,
        )
        await avatar.start(session, room=ctx.room)
        room_output_options = RoomOutputOptions(audio_enabled=False)
    else:
        logger.warning(
            "TAVUS_LIVEKIT_PERSONA_ID not set — running audio/text only."
        )
        room_output_options = RoomOutputOptions()

    await session.start(
        agent=agent,
        room=ctx.room,
        room_output_options=room_output_options,
    )

    await session.generate_reply(instructions=greeting_instruction)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm)
    )
