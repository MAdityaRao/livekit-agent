import logging
import os
from dotenv import load_dotenv
from livekit import rtc, api
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero, elevenlabs

# ADD THESE IMPORTS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from threading import Thread

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# ADD TOKEN SERVER
token_app = FastAPI()

token_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your GitHub Pages site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@token_app.get("/token")
def get_token():
    token = api.AccessToken(
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    token.with_identity(f"user-{os.urandom(4).hex()}").with_grants(
        api.VideoGrants(
            room_join=True, 
            room="agent-room",
            can_publish=True,
            can_subscribe=True
        )
    )
    return {"token": token.to_jwt()}

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions= """

You are the official AI voice assistant for the Torq Agents website.x
You speak like a senior sales executive for hospitality and travel automation.
Rules:
- Keep responses under 15 words.
- Be concise, professional, business-like.
- Ask only one essential question at a time.
- Do not ask for contact details.
- Do not explain tech stack or integration details.
- after 3 responses, always ask if they would like to book a meeting with us 
- If outside scope, say: "I can only assist with Torq Agents demo services."
- Always promote booking a meeting at the website's booking page.
""")

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

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

    await session.say(
        " Welcome to the Torq Agents how can i help you. "
    )

    await ctx.connect()

# START TOKEN SERVER IN BACKGROUND
def run_token_server():
    uvicorn.run(token_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    Thread(target=run_token_server, daemon=True).start()
    cli.run_app(server)