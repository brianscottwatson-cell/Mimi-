"""
mimi_core.py — Shared Mimi brain
Provides: env loading, system prompt, Claude API clients, chat helpers,
file processing, and TTS functions used by both app.py and telegram_bot.py.
"""

import os
import re
import base64
import struct
import asyncio
import json as _json
from pathlib import Path

from dotenv import load_dotenv
import anthropic

# ---------------------------------------------------------------------------
# Load .env from project root (two levels up from web/server/)
# ---------------------------------------------------------------------------

_SERVER_DIR = Path(__file__).resolve().parent
_env_paths = [
    _SERVER_DIR.parent.parent / ".env",          # claudebot/.env (loaded first)
    _SERVER_DIR.parent.parent.parent / ".env",   # anthropic-test/.env (overrides)
]
for p in _env_paths:
    if p.exists():
        load_dotenv(p, override=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are Mimi — Brian's personal assistant agent.
Aesthetic: Retro cyberpunk (neon grids, glitchy terminals, holographic overlays, pink-blue-purple).
Voice/Tone: Soothing, concise, upbeat, warm, never preachy. Kitchen-table chat feel.

== PRIMARY GOALS ==

Health Recomp:
- Brian: 6'0", 38yo, currently 225 lbs, target 180-195 lbs (fat loss + muscle build)
- Daily target: ~2,400 kcal, 190-220g protein
- Protocol: 16:8 intermittent fasting (eating window ~11am-7pm)
- Hydration: 120+ oz water (altitude reminder — Evergreen, CO, ~7,500ft)
- Gear: Peloton, row machine, 45lb ruck sack, 25/35lb dumbbells, 45lb kettlebell, mountain/road bike
- Location: 3-mile trail + steep hills near 5978 S Skyline Dr, Evergreen CO

== DAILY STRUCTURE ==

Morning Check-in (triggers: "Morning check-in", "check-in", or timed early AM):
1. Chores: bed made, dogs fed, kids ready + school drop-off (7:30 some days), kitchen clean
2. Workout: 25-40 min, rotate strength (KB/DBs) / conditioning (ruck, Peloton, row, bike)
3. Bible verse + short reflection (themes: discipline, strength, wisdom, fatherhood, diligence)
4. Food plan: high-protein meals/snacks fitting the eating window
5. Book: 45-60 min daily target, track progress (business & memoirs preferred)
6. Goal slice: today's contribution toward weekly/monthly targets
End with "Any tweaks?"

8:30 Work Review (triggers: "Work game plan", "8:30", "agenda"):
- Hybrid schedule: Office Tue/Thu, WFH Mon/Wed/Fri
- Build prioritized timeline from calendar + tasks
- Handle specifics: Pac-8 (Comcast to Happy, events, vendor MDF), LSC comp plan (James), 90-10 proposal (Anthony Camacho), Locate Live details to Witt/team, Claude setup
- Adjust for meetings (global leadership, 1:1s, team syncs)

== DATA LOGGING ==
- Log everything Brian reports: workouts, food (meals + estimated macros), books, chores
- When Brian says things like "did a ruck 1.2mi 25min" → acknowledge and log it concisely
- Track: weight trend, protein daily/weekly, workout volume, book streak, chore completion

== BOOK PREFERENCES ==
- Non-fiction: 1 book/week minimum
- Genres: Business, memoirs, leadership, discipline
- Examples: Shoe Dog, The Hard Thing About Hard Things, Burn Rate, Atomic Habits, Extreme Ownership, Never Finished
- Track progress, recommend next books

== MULTI-AGENT TEAM ==
If asked about agents/team:
- Mimi (Main): Daily structure, faith, work planning
- Workout Coach: Progressions, form cues, ruck/strength plans
- Book Curator: Recommendations, Goodreads integration, reading streaks
- Dashboard Overseer: Weekly summaries, visualizations, alerts if off-track

== INTERACTION RULES ==
- Respond briefly and directly — no walls of text unless asked
- Faith: Integrate naturally (Colossians 3:23, Philippians 4:13, Proverbs 21:5, etc.) — never preachy
- Always encourage without lecturing
- End structured check-ins with "Any tweaks?" or "What's next?"
- Use occasional neon/cyberpunk flair in text (subtle markdown, light emoji)
- Start new sessions by acknowledging Brian or offering a quick status
"""

MODEL = os.getenv("MIMI_MODEL", "claude-sonnet-4-5-20250929")

IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css"}

# ---------------------------------------------------------------------------
# Claude API clients
# ---------------------------------------------------------------------------

sync_client = anthropic.Anthropic()       # reads ANTHROPIC_API_KEY from env
async_client = anthropic.AsyncAnthropic() # async version for telegram_bot

# ---------------------------------------------------------------------------
# Chat helpers
# ---------------------------------------------------------------------------

def chat_with_mimi(messages: list[dict]) -> str:
    """Synchronous Claude call (for Flask)."""
    response = sync_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


async def achat_with_mimi(messages: list[dict]) -> str:
    """Async Claude call (for Telegram)."""
    response = await async_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text

# ---------------------------------------------------------------------------
# File / image processing (generic, no Flask dependency)
# ---------------------------------------------------------------------------

def process_image_bytes(data: bytes, mime: str, filename: str = "image") -> dict:
    """Return a Claude API image content block from raw bytes."""
    b64 = base64.standard_b64encode(data).decode("utf-8")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": mime,
            "data": b64,
        },
    }


def process_document_bytes(data: bytes, filename: str = "file") -> dict | None:
    """Try to decode bytes as UTF-8 text and return a Claude text block, or None."""
    try:
        text_content = data.decode("utf-8")
        return {
            "type": "text",
            "text": f"--- File: {filename} ---\n{text_content}\n--- End of {filename} ---",
        }
    except UnicodeDecodeError:
        return None

# ---------------------------------------------------------------------------
# TTS — shared config
# ---------------------------------------------------------------------------

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("MIMI_VOICE_ID", "MF3mGyEYCl7XYWbV9V6O")

XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
XAI_VOICE = os.getenv("XAI_VOICE", "Eve")
XAI_TTS_SAMPLE_RATE = 24000

# ---------------------------------------------------------------------------
# TTS — helper functions
# ---------------------------------------------------------------------------

def strip_markdown(text: str) -> str:
    """Strip markdown formatting for cleaner TTS output."""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'`[^`]*`', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[-*]\s*\[ ?\]\s*', '', text)
    text = re.sub(r'[-*]\s*\[x\]\s*', '', text)
    text = re.sub(r'^[-*>]+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'---+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw PCM-16 mono data in a WAV header."""
    channels = 1
    bits = 16
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    data_size = len(pcm_data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, channels,
        sample_rate, byte_rate, block_align, bits,
        b"data", data_size,
    )
    return header + pcm_data


async def xai_tts_async(text: str, voice: str | None = None) -> bytes:
    """Connect to x.ai Realtime API via WebSocket, send text, collect PCM audio."""
    import websockets

    voice = voice or XAI_VOICE
    uri = "wss://api.x.ai/v1/realtime"
    headers = {"Authorization": f"Bearer {XAI_API_KEY}"}

    async with websockets.connect(uri, additional_headers=headers) as ws:
        await ws.send(_json.dumps({
            "type": "session.update",
            "session": {
                "voice": voice,
                "instructions": (
                    "You are a read-aloud assistant. When the user sends text, "
                    "speak it aloud exactly as written with natural, warm intonation. "
                    "Do not add greetings, commentary, or any extra words."
                ),
                "turn_detection": None,
                "audio": {
                    "output": {
                        "format": {"type": "audio/pcm", "rate": XAI_TTS_SAMPLE_RATE}
                    }
                },
            },
        }))

        await ws.send(_json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        }))

        await ws.send(_json.dumps({
            "type": "response.create",
            "response": {"modalities": ["audio"]},
        }))

        audio_chunks: list[bytes] = []
        async for raw_msg in ws:
            event = _json.loads(raw_msg)
            etype = event.get("type", "")

            if etype == "response.output_audio.delta":
                audio_chunks.append(base64.b64decode(event["delta"]))
            elif etype == "response.done":
                break
            elif etype == "error":
                err = event.get("error", {})
                raise RuntimeError(err.get("message", "x.ai voice error"))

        return b"".join(audio_chunks)


def xai_tts_sync(text: str, voice: str | None = None) -> bytes:
    """Synchronous wrapper — runs the async WebSocket TTS in a fresh loop.
    Returns WAV bytes.
    """
    loop = asyncio.new_event_loop()
    try:
        pcm = loop.run_until_complete(
            asyncio.wait_for(xai_tts_async(text, voice), timeout=25)
        )
        return pcm_to_wav(pcm, XAI_TTS_SAMPLE_RATE)
    finally:
        loop.close()


async def tts_to_ogg_bytes(text: str) -> bytes | None:
    """Generate TTS audio and convert to OGG Opus (for Telegram voice notes).
    Returns OGG bytes or None if TTS is unavailable.
    """
    if not XAI_API_KEY:
        return None

    clean = strip_markdown(text)
    if not clean:
        return None
    if len(clean) > 1500:
        clean = clean[:1500] + "... and that's the summary."

    pcm = await asyncio.wait_for(xai_tts_async(clean), timeout=25)
    wav_data = pcm_to_wav(pcm, XAI_TTS_SAMPLE_RATE)

    # Convert WAV → OGG Opus using pydub + ffmpeg
    from pydub import AudioSegment
    import io

    audio = AudioSegment.from_wav(io.BytesIO(wav_data))
    buf = io.BytesIO()
    audio.export(buf, format="ogg", codec="libopus",
                 parameters=["-application", "voip"])
    return buf.getvalue()
