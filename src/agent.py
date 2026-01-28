import logging
import json
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference, room_io, utils
)
from livekit.plugins import noise_cancellation, silero, elevenlabs
# IMPORT YOUR TOOLS HERE
from tools import HotelAssistant 

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# --- PROMPTS ---
PROMPT_TORQ = """
ou are the official AI voice assistant for the Torq Agents website.

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
"""

PROMPT_HOTEL = """
You are a Senior Reservations Executive at the prestigious Demo Hotel.
Your demeanor is professional, warm, and highly efficient.

**Operational Rules:**
1. **Pricing:** All rooms are strictly **5,000 INR per night**. Do not negotiate.
2. **Booking Requirements:** You MUST obtain these 4 specific details before confirming a booking:
   - Full Name
   - Phone Number
   - Check-in Date
   - Check-out Date
3. **Process:**
   - Briefly confirm availability for their dates.
   - Quote the total price based on the 5,000 INR/night rate.
   - Collect missing details one by one to avoid overwhelming the guest.
   - Once all 4 details are collected, use the `book_room` tool to finalize.
"""

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    # 1. Connect to the Room
    await ctx.connect()
    
    logger.info(f"Waiting for participant in room {ctx.room.name}")
    participant = await utils.wait_for_participant(ctx.room)
    logger.info(f"Participant joined: {participant.identity}")

    # 2. Detect Source Website (Torq vs Hotel)
    initial_prompt = PROMPT_TORQ
    source = "unknown"
    f_context = None

    if participant.metadata:
        try:
            meta = json.loads(participant.metadata)
            source = meta.get("source_website", "torq_website")
        except:
            logger.warn("Could not parse metadata")

    # 3. Switch Persona & Enable Tools
    if source == "hotel_demo":
        logger.info("Loading Hotel Persona")
        initial_prompt = PROMPT_HOTEL
        f_context = HotelAssistant() # <--- Only give tools to the Hotel Agent
    else:
        logger.info("Loading Torq Persona")
        initial_prompt = PROMPT_TORQ
        f_context = None 

    # 4. Initialize the Brain
    session = AgentSession(
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        llm=inference.LLM(
            model="openai/gpt-4o-mini", 
            function_context=f_context
        ),
        tts=inference.TTS(model="elevenlabs/eleven_flash_v2", language="en"),
        # VAD is critical so the agent knows when you stop talking
        turn_detection=inference.VADSTTDetector(vad=ctx.proc.userdata["vad"]), 
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # 5. Define the Agent Wrapper
    class DynamicAssistant(Agent):
        def __init__(self, prompt):
            super().__init__(instructions=prompt)

    # 6. Start the Session
    await session.start(
        agent=DynamicAssistant(initial_prompt),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    # 7. Say the Greeting
    greeting = ""
    if source == "hotel_demo":
        greeting = "Welcome to Demo Hotel. How can I assist with your reservation today?"
    else:
        greeting = "Welcome to Torq Agents. How can I help you automate your business?"

    # We use allow_interruptions=False to ensure the full greeting is spoken
    await session.say(greeting, allow_interruptions=False)

if __name__ == "__main__":
    cli.run_app(server)