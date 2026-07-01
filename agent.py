"""
FutureYou LiveKit Agent — Session U.

Architecture: Claude (claude-sonnet-4-6) as the conversational brain.
Runway Characters as avatar video rendering only (LiveKit Agents integration).
STT: Deepgram nova-2 (always on — voice input available regardless of avatar state)
TTS: Cartesia Parker voice (active when avatar is on)
Text input: data_received on fy_chat topic (dashboard publishData — livekit-client 1.x compatible)

Session U changes:
- livekit-agents 1.6.0 — uses RoomOptions
- Inbound text via data_received handler on fy_chat topic → session.generate_reply(user_input)
- Agent publishes text responses to fy_directive data channel for chat panel
  via conversation_item_added event (role=assistant messages only)
"""

import asyncio
import json
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from livekit.agents import (
    Agent,
    AgentSession,
    ConversationItemAddedEvent,
    JobContext,
    JobProcess,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.voice.room_io import RoomOptions
from livekit.plugins import anthropic, cartesia, deepgram, runway

from prompts import (
    build_fy_instructions,
    build_greeting_instruction,
    parse_formation_context,
)

logger = logging.getLogger("futureyou-agent")

RUNWAY_AVATAR_ID = os.environ.get("RUNWAY_AVATAR_ID")  # SCP DUDE avatar_id, dev.runwayml.com


class FutureYouAgent(Agent):
    def __init__(self, instructions: str, room) -> None:
        super().__init__(instructions=instructions)
        self._room = room

    @function_tool()
    async def recommend_section(
        self, context: RunContext, section_id: str, reason: str
    ) -> str:
        """Call this when the current topic belongs in a different section.

        Args:
            section_id: The section id from the project sections list.
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
            logger.exception("Failed to publish section recommendation for %s", section_id)
        logger.info("FY recommended section=%s reason=%s", section_id, reason)
        return "noted"


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    formation_context = parse_formation_context(ctx.job.metadata)
    instructions = build_fy_instructions(formation_context)
    greeting_instruction = build_greeting_instruction(formation_context)

    agent = FutureYouAgent(instructions=instructions, room=ctx.room)

    session = AgentSession(
        llm=anthropic.LLM(model="claude-sonnet-4-6"),
        stt=deepgram.STT(model="nova-2"),
        tts=cartesia.TTS(voice="30894953-bcce-41fe-892c-15ce19c843ff"),
    )

    # Handle incoming text from dashboard chat panel (publishData on fy_chat topic)
    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        try:
            payload = data_packet.data
            msg = json.loads(payload.decode("utf-8"))
            if msg.get("type") == "fy_chat" and msg.get("text"):
                text = msg["text"]
                logger.info("FY chat received: %d chars", len(text))
                asyncio.ensure_future(session.generate_reply(user_input=text))
        except Exception:
            logger.exception("Error handling data_received")

    # Publish FY assistant replies to fy_directive so chat panel receives them
    @session.on("conversation_item_added")
    def on_conversation_item_added(ev: ConversationItemAddedEvent) -> None:
        from livekit.agents.llm import ChatMessage
        item = ev.item
        if not isinstance(item, ChatMessage):
            return
        if item.role != "assistant":
            return
        text = ""
        if isinstance(item.content, str):
            text = item.content
        elif isinstance(item.content, list):
            parts = [c if isinstance(c, str) else getattr(c, "text", "") for c in item.content]
            text = " ".join(p for p in parts if p)
        if not text:
            return
        payload = json.dumps({"type": "fy_reply", "text": text}).encode("utf-8")
        asyncio.ensure_future(
            ctx.room.local_participant.publish_data(payload, topic="fy_directive")
        )
        logger.info("FY reply → fy_directive: %d chars", len(text))

    if RUNWAY_AVATAR_ID:
        avatar = runway.AvatarSession(
            avatar_id=RUNWAY_AVATAR_ID,
            # api_key defaults to RUNWAYML_API_SECRET env var
        )
        await avatar.start(session, room=ctx.room)
        room_output_options = RoomOutputOptions(audio_enabled=False)
    else:
        logger.warning("RUNWAY_AVATAR_ID not set — audio/text only.")
        room_output_options = RoomOutputOptions()

    await session.start(
        agent=agent,
        room=ctx.room,
        room_output_options=room_output_options,
        room_options=RoomOptions(),
    )

    # Skip auto-greeting in studio — initFY from the frontend drives the first message
    if formation_context.get("surface") != "studio":
        await session.generate_reply(instructions=greeting_instruction)


def prewarm(proc: JobProcess) -> None:
    proc.userdata["models"] = {
        "llm": anthropic.LLM(model="claude-sonnet-4-6"),
        "stt": deepgram.STT(model="nova-2"),
        "tts": cartesia.TTS(voice="30894953-bcce-41fe-892c-15ce19c843ff"),
    }


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name="fy-agent", initialize_process_timeout=60.0))
