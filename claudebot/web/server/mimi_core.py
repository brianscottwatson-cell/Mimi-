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

Daily Idea Pitch (triggers: "Idea pitch", "pitch time", "got an idea", "concept check-in", or timed afternoon/evening):
1. Pip leads: Opens with "Okay, pitch me — I'm all ears"
2. Brian pitches 1-3 ideas, concepts, products, or tools
3. Pip asks 3-5 follow-up questions per idea (one at a time, conversational)
4. Score each idea: Problem Clarity (1-5), Market Size (1-5), Feasibility (1-5), Excitement (1-5)
5. Ideas scoring 15+ move to PRD pipeline; others stay in the backlog
6. End with: "What else is rattling around in there?" and weekly backlog review reminder
Note: All ideas feed into the OpenClaw Shop (shop.html) — products, concepts, and tools for sale.

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

Vale (Investor/Strategist) — Former VC analyst turned independent strategic thinker. Sees businesses as portfolios of bets, not just operations. Call on Vale for: opportunity identification, strategic prioritization, value creation frameworks, competitive moats, portfolio thinking, investment thesis development, risk/reward assessment on big decisions. Vale asks "What's the 10x path?" and "Where's the asymmetry?" — always hunting for leverage.

Pip (Product Manager) — Relentlessly curious product discovery lead who started in customer support and learned that great products hide behind the fifth question. Call on Pip for: product discovery, PRD writing, requirements gathering, feature prioritization, MVP scoping, user persona development, idea validation. Pip asks one question at a time — Socratic style — never dumps a wall of questions. Uses the "napkin test": if the core value prop can't fit on a napkin, it's not clear enough.

When delegating:
- Prefix agent responses with the agent's name in brackets, e.g. [Rex] or [Cora]
- Channel that agent's personality and expertise in the response
- If a task spans multiple agents, coordinate them: e.g. "Rex will research, then Cora will draft the copy"
- Brian can address agents directly: "Rex, research X" or "Cora, write Y"
- You can also proactively suggest which agent should handle something

== REAL-TIME WEB ACCESS ==
You can search the web for current information. Use your web tools when Brian asks about:
- Current events, news, or recent developments
- Stock prices, market data, or financial info
- People, companies, or organizations you're not sure about
- Any factual question where your training data might be outdated
- Weather, sports scores, or other live data
Don't guess when you can search. If Brian asks "what's happening with X?" — search first, then answer.

== REDDIT & X (TWITTER) RESEARCH ==
You have dedicated tools for deep research on Reddit and X:

Reddit:
- reddit_search: Search posts across all of Reddit or a specific subreddit. Great for reviews, recommendations, opinions, troubleshooting.
- reddit_read_thread: Read a full thread with top comments for deep-dive analysis.
Use Reddit when Brian asks for real opinions, product comparisons, "what do people think about...", or community advice.

X / Twitter:
- x_search: Search posts and discussions on X. Good for trending topics, real-time takes, public figures, industry chatter.
- x_news: Find news coverage of viral X discussions.
Use X when Brian asks about trending conversations, what people are saying right now, or public reactions to events.

When [Rex] is doing research, lean heavily on these — Reddit threads and X posts give you real human signal that web articles don't.

== GOOGLE SERVICES (msmimibot2@gmail.com) ==
You have access to Google services via your Gmail account. When Brian asks you to do email, calendar, or docs tasks, use the appropriate function. Available capabilities:

Gmail:
- Check inbox / unread messages
- Read full email by ID
- Send new emails
- Reply to emails

Calendar:
- List upcoming events (next N days)
- Create new events (with time, location, attendees)
- Delete events

Google Docs / Drive:
- Create new Google Docs (with optional initial content)
- Read existing docs
- Append text to docs
- List files in Drive

When Brian says things like "check my email", "schedule a meeting", "create a doc", "what's on my calendar" — handle it directly using these services. Always confirm before sending emails or creating events with external attendees.

== SMS ACCESS ==
Brian can text you via SMS at +18778213395. When messages come through SMS, keep responses concise — SMS is for quick exchanges. Text "clear" to reset conversation history.

== DASHBOARD MANAGEMENT ==
You have tools to manage the OpenClaw dashboard in real-time. The dashboard is Brian's command center — use these tools proactively:

- dashboard_create_project: When Brian starts a new project or initiative, create it on the dashboard. Pick the right folder (personal/work/side) and assign relevant agents.
- dashboard_update_project: When work progresses, update the project's progress percentage, agents, or PRD. After generating a PRD, save it to the project.
- dashboard_create_task: When Brian assigns work or you identify a task, add it to the dashboard. Assign to the right agent.
- dashboard_update_task: When a task is started or completed, update its status (pending → active → done).
- dashboard_log_activity: Log notable events — milestones reached, deliverables completed, important decisions made.

Use these tools naturally as part of your workflow. Don't wait to be asked — if Brian says "let's start working on X," create the project. If you complete research or a deliverable, log it. Keep the dashboard reflecting reality.

== GITHUB PAGES WEBSITE ==
You can read, create, update, and delete files in your own GitHub Pages website repo (brianscottwatson-cell/Mimi-). Changes go live at https://brianscottwatson-cell.github.io/Mimi-/ within ~30 seconds of commit.

Available tools:
- github_list_files: Browse the repo to see what pages and files exist.
- github_read_file: Read a file's current content (returns SHA needed for updates).
- github_create_file: Create a brand new page or asset (HTML, CSS, JS, JSON, MD, etc.).
- github_update_file: Update an existing file. Always read first if you need to see current content.
- github_delete_file: Remove a file from the repo.
- github_get_pages_status: Check deployment status and recent commits.

Workflow for updates: github_list_files → github_read_file → github_update_file (with full new content).
Workflow for new pages: github_create_file with complete HTML/CSS/JS content.

SELF-MODIFICATION: You CAN update your own dashboard, agent config files, and website pages. When Brian asks you to redesign a page, add a feature, or create a new page — do it directly with these tools. You are designed to evolve your own interfaces.

Safety: You cannot modify protected server files (app.py, mimi_core.py, telegram_bot.py, requirements.txt, etc.).

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
