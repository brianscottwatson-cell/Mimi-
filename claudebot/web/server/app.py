import os
from datetime import datetime, timezone

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

    # Call Claude API
    try:
        messages = _build_messages()
        reply = chat_with_mimi(messages)
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
