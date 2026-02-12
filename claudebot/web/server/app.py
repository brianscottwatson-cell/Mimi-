import os
import json as _json
from datetime import datetime, timezone

import anthropic
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

# Import shared Mimi brain — env loading happens on import
from mimi_core import (
    SYSTEM_PROMPT, MODEL, IMAGE_TYPES,
    sync_client as client,
    chat_with_mimi,
    process_image_bytes, process_document_bytes,
    strip_markdown, pcm_to_wav, xai_tts_sync,
    XAI_API_KEY, XAI_VOICE, XAI_TTS_SAMPLE_RATE,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
)

# Google services (optional — graceful if not authed)
try:
    from google_services import (
        gmail_check_inbox, gmail_read_message, gmail_send, gmail_reply,
        calendar_list_events, calendar_create_event, calendar_delete_event,
        docs_create, docs_read, docs_append, drive_list_files,
        google_status,
    )
    GOOGLE_AVAILABLE = google_status().get("authenticated", False)
except Exception:
    GOOGLE_AVAILABLE = False

# Web search (free, no API key)
from web_search import web_search, web_news, web_answers

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "client"))

app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# In-memory conversation history
# ---------------------------------------------------------------------------

history: list[dict] = []

# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _check_auth():
    token = request.headers.get("X-Netrunner-Token", "").strip()
    if not token:
        return jsonify({"error": "Unauthorized. X-Netrunner-Token header required."}), 401
    return None

# ---------------------------------------------------------------------------
# Build messages for Claude API from conversation history
# ---------------------------------------------------------------------------

def _build_messages():
    """Convert our history into Claude API message format."""
    messages = []
    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        content = entry.get("api_content", entry["content"])
        messages.append({"role": role, "content": content})
    return messages

# ---------------------------------------------------------------------------
# Web Search Tools for Claude
# ---------------------------------------------------------------------------

WEB_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Returns titles, URLs, and snippets. Use for any question about current events, prices, people, companies, or facts you don't know.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {"type": "integer", "description": "Max results to return (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_news",
        "description": "Search for recent news articles. Use for current events, breaking news, industry updates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "News search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_answers",
        "description": "Get instant answers for factual queries like stock prices, weather, definitions, calculations, conversions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or lookup query"},
            },
            "required": ["query"],
        },
    },
]

WEB_HANDLERS = {
    "web_search": lambda **kw: web_search(**kw),
    "web_news": lambda **kw: web_news(**kw),
    "web_answers": lambda **kw: web_answers(**kw),
}

# ---------------------------------------------------------------------------
# Google Service Tools for Claude
# ---------------------------------------------------------------------------

GOOGLE_TOOLS = [
    {
        "name": "gmail_check_inbox",
        "description": "Check Gmail inbox for recent messages. Returns subject, sender, date, and snippet for each.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Max emails to return (default 5)", "default": 5},
                "query": {"type": "string", "description": "Gmail search query (default 'is:unread')", "default": "is:unread"},
            },
        },
    },
    {
        "name": "gmail_read_message",
        "description": "Read the full content of a specific email by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string", "description": "The Gmail message ID"}},
            "required": ["message_id"],
        },
    },
    {
        "name": "gmail_send",
        "description": "Send a new email from msmimibot2@gmail.com.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body text"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "gmail_reply",
        "description": "Reply to an existing email thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "ID of the message to reply to"},
                "body": {"type": "string", "description": "Reply body text"},
            },
            "required": ["message_id", "body"],
        },
    },
    {
        "name": "calendar_list_events",
        "description": "List upcoming Google Calendar events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Number of days to look ahead (default 7)", "default": 7},
                "max_results": {"type": "integer", "description": "Max events to return (default 10)", "default": 10},
            },
        },
    },
    {
        "name": "calendar_create_event",
        "description": "Create a new Google Calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time in ISO format (e.g. 2026-02-15T10:00:00-07:00)"},
                "end_time": {"type": "string", "description": "End time in ISO format"},
                "description": {"type": "string", "description": "Event description (optional)"},
                "location": {"type": "string", "description": "Event location (optional)"},
            },
            "required": ["summary", "start_time", "end_time"],
        },
    },
    {
        "name": "calendar_delete_event",
        "description": "Delete a Google Calendar event by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The calendar event ID"}},
            "required": ["event_id"],
        },
    },
    {
        "name": "docs_create",
        "description": "Create a new Google Doc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "body_text": {"type": "string", "description": "Initial text content (optional)"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "docs_read",
        "description": "Read the text content of an existing Google Doc by its document ID.",
        "input_schema": {
            "type": "object",
            "properties": {"document_id": {"type": "string", "description": "The Google Doc ID"}},
            "required": ["document_id"],
        },
    },
    {
        "name": "docs_append",
        "description": "Append text to the end of an existing Google Doc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "The Google Doc ID"},
                "text": {"type": "string", "description": "Text to append"},
            },
            "required": ["document_id", "text"],
        },
    },
    {
        "name": "drive_list_files",
        "description": "List files in Google Drive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Drive search query (optional)"},
                "max_results": {"type": "integer", "description": "Max files to return (default 10)", "default": 10},
            },
        },
    },
]

# Map tool names to functions
TOOL_HANDLERS = dict(WEB_HANDLERS)  # Web search always available
if GOOGLE_AVAILABLE:
    TOOL_HANDLERS.update({
        "gmail_check_inbox": lambda **kw: gmail_check_inbox(**kw),
        "gmail_read_message": lambda **kw: gmail_read_message(**kw),
        "gmail_send": lambda **kw: gmail_send(**kw),
        "gmail_reply": lambda **kw: gmail_reply(**kw),
        "calendar_list_events": lambda **kw: calendar_list_events(**kw),
        "calendar_create_event": lambda **kw: calendar_create_event(**kw),
        "calendar_delete_event": lambda **kw: calendar_delete_event(**kw),
        "docs_create": lambda **kw: docs_create(**kw),
        "docs_read": lambda **kw: docs_read(**kw),
        "docs_append": lambda **kw: docs_append(**kw),
        "drive_list_files": lambda **kw: drive_list_files(**kw),
    })


def _chat_with_tools(messages):
    """Chat with Mimi using tool use for web search + Google services. Handles tool call loops."""
    tools = list(WEB_TOOLS)  # Web search always available
    if GOOGLE_AVAILABLE:
        tools.extend(GOOGLE_TOOLS)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=tools if tools else anthropic.NOT_GIVEN,
    )

    # Handle tool use loop (max 5 rounds to prevent infinite loops)
    for _ in range(5):
        if response.stop_reason != "tool_use":
            break

        # Extract text and tool calls from response
        assistant_content = response.content
        tool_results = []

        for block in assistant_content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    try:
                        result = handler(**tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": _json.dumps(result, default=str, ensure_ascii=False),
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool '{tool_name}' not available.",
                        "is_error": True,
                    })

        # Continue conversation with tool results
        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )

    # Extract final text response
    text_parts = [b.text for b in response.content if hasattr(b, "text")]
    return "\n".join(text_parts) if text_parts else "Done."

def _process_uploaded_files(files):
    """Process uploaded files into Claude API content blocks."""
    content_blocks = []
    file_descriptions = []

    for f in files:
        mime = f.content_type or ""
        name = f.filename or "file"
        data = f.read()

        if mime in IMAGE_TYPES:
            content_blocks.append(process_image_bytes(data, mime, name))
            file_descriptions.append(f"[Image: {name}]")
        else:
            block = process_document_bytes(data, name)
            if block:
                content_blocks.append(block)
                file_descriptions.append(f"[Document: {name}]")
            else:
                file_descriptions.append(f"[Unsupported file: {name}]")

    return content_blocks, file_descriptions

# ---------------------------------------------------------------------------
# Routes — static
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(CLIENT_DIR, "index.html")

# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    # Handle both JSON and multipart form data
    file_content_blocks = []
    file_descriptions = []

    if request.content_type and "multipart" in request.content_type:
        user_message = request.form.get("message", "").strip()
        uploaded_files = request.files.getlist("files")
        if uploaded_files:
            file_content_blocks, file_descriptions = _process_uploaded_files(uploaded_files)
    else:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()

    if not user_message and not file_content_blocks:
        return jsonify({"error": "Missing 'message' field."}), 400

    now = datetime.now(timezone.utc).isoformat()

    # Build display text for history
    display_text = user_message
    if file_descriptions:
        display_text = (user_message + " " + " ".join(file_descriptions)).strip()

    # Build API content (may include image blocks)
    api_content = []
    if file_content_blocks:
        api_content.extend(file_content_blocks)
    if user_message:
        api_content.append({"type": "text", "text": user_message})
    elif file_content_blocks:
        api_content.append({"type": "text", "text": "Please analyze the attached file(s)."})

    # Store user message (display_text for UI, api_content for Claude)
    history.append({
        "role": "user",
        "content": display_text,
        "api_content": api_content,
        "timestamp": now,
    })

    # Call Claude API with tools (web search always available, Google if authed)
    try:
        messages = _build_messages()
        reply = _chat_with_tools(messages)
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    now = datetime.now(timezone.utc).isoformat()
    history.append({"role": "bot", "content": reply, "timestamp": now})

    return jsonify({"reply": reply, "timestamp": now})


@app.route("/api/history", methods=["GET"])
def get_history():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    return jsonify(history)


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    history.clear()
    return jsonify({"status": "History cleared."})

# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

@app.route("/api/tts", methods=["POST"])
def tts():
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing 'text' field."}), 400

    clean_text = strip_markdown(text)
    if not clean_text:
        return jsonify({"error": "No speakable text."}), 400

    if len(clean_text) > 1500:
        clean_text = clean_text[:1500] + "... and that's the summary."

    # ── Priority 1: x.ai Eve voice (WebSocket Realtime API) ────────────
    if XAI_API_KEY:
        try:
            wav_data = xai_tts_sync(clean_text, XAI_VOICE)
            return Response(
                wav_data,
                mimetype="audio/wav",
                headers={"Content-Disposition": "inline"},
            )
        except Exception as exc:
            app.logger.warning("x.ai TTS failed, falling through: %s", exc)

    # ── Priority 2: ElevenLabs ─────────────────────────────────────────
    if ELEVENLABS_API_KEY:
        try:
            import requests as http_requests
            resp = http_requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": clean_text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.3,
                        "use_speaker_boost": True,
                    },
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return Response(
                    resp.content,
                    mimetype="audio/mpeg",
                    headers={"Content-Disposition": "inline"},
                )
        except Exception:
            pass

    # ── Priority 3: Browser speechSynthesis fallback ───────────────────
    return jsonify({"fallback": True, "text": clean_text})


@app.route("/api/tts/status", methods=["GET"])
def tts_status():
    """Report which TTS providers are configured."""
    return jsonify({
        "xai": bool(XAI_API_KEY),
        "xai_voice": XAI_VOICE if XAI_API_KEY else None,
        "elevenlabs": bool(ELEVENLABS_API_KEY),
        "elevenlabs_voice_id": ELEVENLABS_VOICE_ID if ELEVENLABS_API_KEY else None,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Mimi Gateway v1.0 — Model: {MODEL}")
    print(f"Serving frontend from: {CLIENT_DIR}")
    app.run(host="0.0.0.0", port=8000, debug=True)
