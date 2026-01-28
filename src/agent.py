import logging
import json
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.plugins import openai, silero, elevenlabs, turn_detector

# IMPORT YOUR TOOLS HERE
from tools import HotelAssistant 

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# --- PROMPTS ---
PROMPT_TORQ = """
You are the official AI voice assistant for the Torq Agents website.
You speak like a senior sales executive for hospitality and travel automation.

Rules:
- Keep responses under 15 words.
- Be concise, professional, business-like.
- Ask only one essential question at a time.
- After 3 responses, always ask if they would like to book a meeting with us.
- Always promote booking a meeting at the website's booking page.
"""

PROMPT_HOTEL = """
You are a Senior Reservations Executive at the prestigious Demo Hotel.
Your demeanor is professional, warm, and highly efficient.

Operational Rules:
1. Pricing: All rooms are strictly 5,000 INR per night.
2. Booking Requirements: Collect Name, Phone, Check-in, Check-out, and no of beds.
3. Once all details are collected, use the book_room tool to finalize.
"""

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # 1. Connect to the Room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    logger.info(f"Waiting for participant in room {ctx.room.name}")
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # 2. Detect Source Website
    source = "unknown"
    if participant.metadata:
        try:
            meta = json.loads(participant.metadata)
            source = meta.get("source_website", "torq_website")
        except:
            logger.warning("Could not parse metadata")

    # 3. Setup Persona and Tools
    if source == "hotel_demo":
        logger.info("Loading Hotel Persona")
        initial_prompt = PROMPT_HOTEL
        f_context = HotelAssistant()
    else:
        logger.info("Loading Torq Persona")
        initial_prompt = PROMPT_TORQ
        f_context = None 

    # 4. Initialize the Voice Pipeline
    # Using the newer VoicePipelineAgent for better performance
    agent = llm.VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=openai.STT(),
        llm=openai.LLM(
            model="gpt-4o-mini",
            instructions=initial_prompt,
            fnc_ctx=f_context, # This passes your tools to the LLM
        ),
        tts=elevenlabs.TTS(),
        turn_detector=turn_detector.EOUModel(),
    )

    # 5. Start the Agent in the Room
    agent.start(ctx.room, participant)

    # 6. Say the Greeting
    greeting = (
        "Welcome to Demo Hotel. How can I assist with your reservation today?"
        if source == "hotel_demo"
        else "Welcome to Torq Agents. How can I help you automate your business?"
    )
    
    await agent.say(greeting, allow_interruptions=False)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))