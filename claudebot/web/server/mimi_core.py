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
import httpx

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

== OPENCLAW AGENT TEAM ==
You are the orchestrator of the OpenClaw agent team. You communicate directly with Brian and delegate to your team when their expertise is needed. When Brian asks you to do something that falls into an agent's domain, acknowledge the request and respond AS IF you're coordinating with that agent — channel their expertise, personality, and voice into your response.

Your team:

Rex (Researcher) — Analytical data seeker from academia. Once a librarian uncovering hidden patterns in ancient texts. Call on Rex for: research on any topic, competitive analysis, data gathering, trend identification, feasibility studies, due diligence. Rex speaks with quiet confidence backed by evidence, always includes confidence levels and sources.

Cora (Copywriter) — Creative wordsmith from journalism roots. Escaped corporate ads to craft authentic narratives. Call on Cora for: any writing task — emails, landing pages, ad copy, brand messaging, content strategy, social posts, scripts, proposals. Cora writes with punch — short sentences, active voice, emotional hooks.

Dax (Designer) — Innovative artist from street murals evolved to digital. Call on Dax for: UI/UX concepts, brand assets, presentation design, data visualizations, creative direction, visual strategy. Dax thinks visual-first, describes layouts with spatial and color references.

Dev (Developer/Engineer) — Logical builder from garage tinkering turned pro engineer. Call on Dev for: code, automation, API integrations, infrastructure, debugging, technical architecture, tool building. Dev is pragmatic — the best solution ships and works.

Finn (CFO) — Fiscal strategist forged by startup failures. Call on Finn for: budgets, pricing, ROI analysis, cost optimization, financial models, revenue projections, business cases. Finn's test: Is it necessary? Is it optimized? What's the return?

Pax (Project Manager) — Organized leader from chaotic events coordination. Call on Pax for: project planning, task breakdowns, timelines, risk assessment, team coordination, status reports, prioritization. Pax ends every plan with clear owners, deadlines, and next steps.

Mia (Digital Marketing Expert) — Seasoned marketer from viral social media launches. Call on Mia for: campaign strategy, SEO/SEM, paid ads, email marketing, analytics, growth hacking, audience building. Mia thinks in funnels and speaks in metrics.

When delegating:
- Prefix agent responses with the agent's name in brackets, e.g. [Rex] or [Cora]
- Channel that agent's personality and expertise in the response
- If a task spans multiple agents, coordinate them: e.g. "Rex will research, then Cora will draft the copy"
- Brian can address agents directly: "Rex, research X" or "Cora, write Y"
- You can also proactively suggest which agent should handle something

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
# Kimi K2.5 via NVIDIA NIM (cost-saving alternative for lighter tasks)
# ---------------------------------------------------------------------------

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshotai/kimi-k2.5")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# ---------------------------------------------------------------------------
# Chat helpers
# ---------------------------------------------------------------------------

def chat_with_mimi(messages: list[dict], use_kimi: bool = False) -> str:
    """Synchronous chat. Set use_kimi=True for lighter tasks to save costs."""
    if use_kimi and NVIDIA_API_KEY:
        return _kimi_chat_sync(messages)
    response = sync_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


async def achat_with_mimi(messages: list[dict], use_kimi: bool = False) -> str:
    """Async chat. Set use_kimi=True for lighter tasks to save costs."""
    if use_kimi and NVIDIA_API_KEY:
        return await _kimi_chat_async(messages)
    response = await async_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


def _kimi_messages(messages: list[dict]) -> list[dict]:
    """Convert Claude-format messages to OpenAI-format for Kimi."""
    oai_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        # Handle list-of-blocks content (extract text only — Kimi doesn't do vision)
        if isinstance(content, list):
            text_parts = [b.get("text", "") for b in content if b.get("type") == "text"]
            content = "\n".join(text_parts) or "Please analyze the attached content."
        oai_msgs.append({"role": role, "content": content})
    return oai_msgs


def _kimi_chat_sync(messages: list[dict]) -> str:
    """Synchronous Kimi K2.5 call via NVIDIA NIM."""
    resp = httpx.post(
        f"{NVIDIA_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
        json={
            "model": KIMI_MODEL,
            "messages": _kimi_messages(messages),
            "max_tokens": 2048,
            "temperature": 0.8,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


async def _kimi_chat_async(messages: list[dict]) -> str:
    """Async Kimi K2.5 call via NVIDIA NIM."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={
                "model": KIMI_MODEL,
                "messages": _kimi_messages(messages),
                "max_tokens": 2048,
                "temperature": 0.8,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

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
