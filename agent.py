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

Session AC change:
- fy_avatar_control topic (data_received) toggles the live Runway AvatarSession
  on/off. Runway bills per active-session-time (2 credits / 6s), not per
  utterance, so this closes/reopens the AvatarSession rather than just muting —
  that's the only way to actually stop the charge mid-conversation.

Session AD change:
- Proactive avatar session rotation. Runway Characters sessions hard-cap at
  5 minutes platform-side (confirmed via Runway docs; not client-settable,
  and the installed plugin has no renew/extend call — only a creation-time
  max_duration). Any conversation running past ~5 min drops the avatar with
  no recovery. Fix: close and reopen a fresh AvatarSession every
  AVATAR_ROTATION_SECONDS (270s, 30s margin before the cap), reusing the
  Session AC billing-stop close/reopen plumbing. Rotation is cancelled
  cleanly on manual toggle-off so it doesn't fire against a closed session.
- Cartesia pronunciation_dict_id and speed wired via env vars
  (CARTESIA_PRONUNCIATION_DICT_ID, CARTESIA_TTS_SPEED). Neither is
  verifiable from this side — both require Lee to test by ear — so they're
  tunable without a code change rather than hardcoded to a guessed value.
  Both only take effect on sonic-3 (already this project's default model).
- Switched model sonic-3 -> sonic-3.5 and voice Parker -> Jameson
  (a5136bf9-224c-4d76-b823-52bd5efcffcc, en-US male), per Cartesia's own
  docs: sonic-3.5 claims "dramatically better alphanumeric read-out" and
  fixed English heteronym pronunciation in context — direct match for the
  mispronunciation reports on this project. Documented as a drop-in
  replacement (same voice IDs, same request shape). Tradeoff: speed/volume
  controls are temporarily disabled on sonic-3.5 per Cartesia's migration
  notes, so CARTESIA_TTS_SPEED is currently a no-op — left wired since it's
  harmless and matters again if this ever reverts to sonic-3. Unverified
  until Lee hears it live.
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

# Session AD: pronunciation dict + speed are env-driven, not hardcoded — neither
# is verifiable without hearing the actual audio output, so these need Lee to
# test values by ear rather than Claude picking a number blind. Both only take
# effect on sonic-3 (already the plugin default). Empty/unset = no change from
# current behavior.
CARTESIA_PRONUNCIATION_DICT_ID = os.environ.get("CARTESIA_PRONUNCIATION_DICT_ID") or None
_raw_speed = os.environ.get("CARTESIA_TTS_SPEED")
CARTESIA_TTS_SPEED = float(_raw_speed) if _raw_speed else None


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

    @function_tool()
    async def capture_vault_entry(
        self,
        context: RunContext,
        building_slug: str,
        section_name: str,
        step_title: str,
        captured_answer: str,
    ) -> str:
        """Call this when the creator's answer to the current step's open
        question has been refined into something concrete and usable — not
        a first pass, not a one-word answer, but something you could hand to
        a collaborator and have it mean something. Set a fairly wide bar:
        it doesn't need to be a finished or perfect answer, just something
        you can actually interpret that genuinely satisfies what the step
        asked. Don't call this for a raw first response that still needs
        refining — keep working it with the creator until it lands, then
        call this once, with your own distilled version of the answer, not
        a verbatim quote of what they said.

        Args:
            building_slug: The building id (e.g. "ideate").
            section_name: The exact section name (e.g. "Raw Idea").
            step_title: The exact step title (e.g. "What's the Feeling?").
            captured_answer: Your synthesized, refined version of what was
                established — in your own words, capturing the real answer
                the back-and-forth landed on.
        """
        payload = json.dumps(
            {
                "type": "fy_vault_capture",
                "building_slug": building_slug,
                "section_name": section_name,
                "step_title": step_title,
                "captured_answer": captured_answer,
            }
        ).encode("utf-8")
        try:
            await self._room.local_participant.publish_data(
                payload, topic="fy_directive"
            )
        except Exception:
            logger.exception(
                "Failed to publish vault capture for %s / %s", section_name, step_title
            )
        logger.info(
            "FY captured vault entry: building=%s section=%s step=%s",
            building_slug, section_name, step_title,
        )
        return "captured"

    @function_tool()
    async def generate_visual(
        self, context: RunContext, task_title: str, visual_prompt: str
    ) -> str:
        """Call this when a step calls for a generated image (e.g. "First
        Visual Instinct") and you and the creator have landed on a specific,
        confirmed visual direction. This is the ONLY way to actually
        produce the visual — you have no other tool and no ability to
        generate it yourself outside this call. Never tell the creator you
        can't call the generator or that they need to do it themselves;
        call this tool instead and let the canvas show the result.

        Args:
            task_title: The exact step title this generation is for (e.g.
                "First Visual Instinct") — must match the step's title
                exactly so the canvas knows which step's generator to use.
            visual_prompt: Your own distilled description of the visual —
                subject, setting, mood, lighting, style — written in your
                own words from the conversation, not a verbatim quote.
        """
        payload = json.dumps(
            {
                "type": "fy_generate_visual",
                "task_title": task_title,
                "visual_prompt": visual_prompt,
            }
        ).encode("utf-8")
        try:
            await self._room.local_participant.publish_data(
                payload, topic="fy_directive"
            )
        except Exception:
            logger.exception(
                "Failed to publish generate_visual for %s", task_title
            )
        logger.info("FY triggered visual generation: task=%s", task_title)
        return "Generation started — tell the creator to watch the canvas, do not say you can't do this yourself."


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    formation_context = parse_formation_context(ctx.job.metadata)
    instructions = build_fy_instructions(formation_context)
    greeting_instruction = build_greeting_instruction(formation_context)

    agent = FutureYouAgent(instructions=instructions, room=ctx.room)

    session = AgentSession(
        llm=anthropic.LLM(model="claude-sonnet-4-6"),
        stt=deepgram.STT(model="nova-2"),
        tts=cartesia.TTS(
            model="sonic-3",
            voice="630ed21c-2c5c-41cf-9d82-10a7fd668370",  # Corey - Supportive Buddy, en-US male
            pronunciation_dict_id=CARTESIA_PRONUNCIATION_DICT_ID,
            speed=CARTESIA_TTS_SPEED,
        ),
    )

    # avatar_state holds the live runway.AvatarSession (or None when toggled off).
    # Runway bills 2 credits upfront + 2 credits per 6s of ACTIVE avatar-session
    # time — not per utterance — so muting playback client-side does nothing to
    # stop the charge. The only documented way to stop billing mid-session is to
    # close the AvatarSession (same path the plugin runs on normal job shutdown);
    # toggling back on means starting a fresh AvatarSession instance.
    #
    # Session AD: Runway Characters sessions hard-cap at 5 minutes, platform-side
    # (confirmed via Runway's own docs — not a client-settable limit, and the
    # installed plugin (1.6.4) has no renew/extend endpoint, only a creation-time
    # max_duration). The only fix is rotation: close and reopen a fresh
    # AvatarSession a safety margin before the cap. rotation_task holds the
    # scheduled rotation so a manual toggle-off can cancel it cleanly.
    AVATAR_ROTATION_SECONDS = 270  # 30s margin before Runway's 300s hard cap

    avatar_state = {"session": None, "lock": asyncio.Lock(), "rotation_task": None}

    def _cancel_rotation_task():
        t = avatar_state.get("rotation_task")
        avatar_state["rotation_task"] = None
        if t is not None and not t.done():
            t.cancel()

    async def _schedule_rotation():
        _cancel_rotation_task()
        avatar_state["rotation_task"] = asyncio.ensure_future(_rotate_after_delay())

    async def _rotate_after_delay():
        try:
            await asyncio.sleep(AVATAR_ROTATION_SECONDS)
        except asyncio.CancelledError:
            return
        # Clear our own ref before acting so the reopen's _schedule_rotation()
        # doesn't try to cancel the task that's already finished sleeping.
        avatar_state["rotation_task"] = None
        logger.info("Avatar rotation: proactively closing/reopening before Runway's cap")
        await _close_avatar_session()
        await _open_avatar_session()

    async def _open_avatar_session():
        async with avatar_state["lock"]:
            if avatar_state["session"] is not None or not RUNWAY_AVATAR_ID:
                return
            av = runway.AvatarSession(avatar_id=RUNWAY_AVATAR_ID)
            await av.start(session, room=ctx.room)
            avatar_state["session"] = av
            logger.info("Avatar session started")
        await _schedule_rotation()

    async def _close_avatar_session():
        async with avatar_state["lock"]:
            av = avatar_state["session"]
            if av is None:
                return
            avatar_state["session"] = None
            try:
                await av.aclose()
                logger.info("Avatar session closed — Runway billing stopped")
            except Exception:
                logger.exception("Error closing avatar session")

    async def start_avatar():
        await _open_avatar_session()

    async def stop_avatar():
        _cancel_rotation_task()
        await _close_avatar_session()

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
            elif msg.get("type") == "fy_say_verbatim" and msg.get("text"):
                # Direct TTS, no LLM turn — for scripted lines (e.g. the triage
                # handoff line) that must be spoken exactly, not decided on by
                # the model. generate_reply()+a "[SPOKEN LINE]" text hack was
                # the old approach; the model had no system-prompt awareness of
                # that convention and would truncate/paraphrase instead of
                # reciting verbatim. session.say() bypasses the LLM entirely.
                text = msg["text"]
                logger.info("FY say-verbatim received: %d chars", len(text))
                asyncio.ensure_future(session.say(text, allow_interruptions=False))
            elif msg.get("type") == "fy_avatar_control":
                enabled = bool(msg.get("on"))
                logger.info("Avatar toggle received: on=%s", enabled)
                asyncio.ensure_future(start_avatar() if enabled else stop_avatar())
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
        await start_avatar()
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
        "tts": cartesia.TTS(
            model="sonic-3",
            voice="630ed21c-2c5c-41cf-9d82-10a7fd668370",
            pronunciation_dict_id=CARTESIA_PRONUNCIATION_DICT_ID,
            speed=CARTESIA_TTS_SPEED,
        ),
    }


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name="fy-agent", initialize_process_timeout=60.0))
