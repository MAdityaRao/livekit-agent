import logging
import os
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
    utils, # Added utils for wait_for_participant
)
from livekit.plugins import noise_cancellation, silero, elevenlabs

logger = logging.getLogger("agent")
load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are the official AI voice assistant for the Torq Agents website.
You speak like a senior sales executive for hospitality and travel automation.
Rules:
- Keep responses under 15 words.
- Be concise, professional, business-like.
- Ask only one essential question at a time.
- Do not ask for contact details.
- Do not explain tech stack or integration details.
- After 3 responses, always ask if they would like to book a meeting with us.
- If outside scope, say: "I can only assist with Torq Agents demo services."
- Always promote booking a meeting at the website's booking page.
""")

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    # Connect to the room
    await ctx.connect()
    
    # Wait for the user to actually join before speaking
    logger.info(f"Waiting for participant in room {ctx.room.name}")
    participant = await utils.wait_for_participant(ctx.room)
    
    logger.info(f"Participant joined: {participant.identity}")

    session = AgentSession(
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="elevenlabs/eleven_flash_v2", language="en"),
        turn_detection=None,
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.say("Welcome to Torq Agents, how can I help you?")

if __name__ == "__main__":
    cli.run_app(server)