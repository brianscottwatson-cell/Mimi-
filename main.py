"""
Mimi — Open Claw Agent
A cyberpunk-styled AI assistant built on the Open Claw framework.
"""

import os
import json
import yaml
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# Load agent configuration
CONFIG_PATH = Path(__file__).parent / "agent_config.yaml"
SOUL_PATH = Path(__file__).parent / "mimi.soul"

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

soul_content = ""
if SOUL_PATH.exists():
    soul_content = SOUL_PATH.read_text()

SYSTEM_PROMPT = config["personality"]["system_prompt"]
GREETING = config["personality"]["greeting"]
MODEL_ID = config["model"]["model_id"]
MAX_TOKENS = config["model"]["max_tokens"]
TEMPERATURE = config["model"]["temperature"]
MAX_HISTORY = config["features"]["max_history_messages"]

# In-memory conversation store (per-session)
conversations: dict[str, list[dict]] = {}


def get_anthropic_client():
    """Lazy-load the Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/chat")
def chat_page():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "agent": config["agent"]["name"],
        "version": config["agent"]["version"],
        "framework": config["agent"]["framework"],
    })


@app.route("/api/soul")
def get_soul():
    return jsonify({
        "name": config["agent"]["name"],
        "soul": soul_content,
        "greeting": GREETING,
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id", "default")
    stream = data.get("stream", False)

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    history = conversations[conversation_id]

    # Add user message
    history.append({"role": "user", "content": user_message})

    # Trim history if needed
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
        conversations[conversation_id] = history

    client = get_anthropic_client()

    if client is None:
        # Fallback: respond in-character without an API key
        fallback = _fallback_response(user_message, history)
        history.append({"role": "assistant", "content": fallback})
        return jsonify({
            "response": fallback,
            "conversation_id": conversation_id,
            "agent": "mimi",
        })

    if stream:
        return Response(
            stream_with_context(_stream_response(client, history, conversation_id)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # Standard (non-streaming) response
    try:
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        assistant_message = response.content[0].text
        history.append({"role": "assistant", "content": assistant_message})

        return jsonify({
            "response": assistant_message,
            "conversation_id": conversation_id,
            "agent": "mimi",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _stream_response(client, history, conversation_id):
    """Stream response using server-sent events."""
    try:
        full_response = ""
        with client.messages.stream(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=history,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield f"data: {json.dumps({'type': 'content', 'text': text})}\n\n"

        history.append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'type': 'done', 'full_text': full_response})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


def _fallback_response(user_message: str, history: list) -> str:
    """In-character fallback when no API key is configured."""
    msg = user_message.lower()

    if any(greet in msg for greet in ["hello", "hi", "hey", "sup", "yo"]):
        return GREETING

    if "who are you" in msg or "what are you" in msg:
        return (
            "I'm Mimi — an Open Claw AI agent. Cyberpunk vibes, real results. "
            "I help with code, ideas, research, and whatever you need to build. "
            "Right now I'm running in offline mode though — hook up an Anthropic API key "
            "and I'll really come alive."
        )

    if "help" in msg:
        return (
            "Here's what I can do once I'm fully connected:\n\n"
            "- **Code** — write, debug, review, explain\n"
            "- **Research** — dig into topics and synthesize answers\n"
            "- **Create** — brainstorm, write, design solutions\n"
            "- **Plan** — break down tasks, map out projects\n\n"
            "Set the `ANTHROPIC_API_KEY` environment variable and I'll be fully operational. "
            "Until then, I'm here in spirit."
        )

    return (
        "I'm running in offline mode right now — no API key configured. "
        "Set `ANTHROPIC_API_KEY` in your environment and restart me, "
        "and I'll be able to actually think through problems with you. "
        "Until then, I'm just vibes and static responses."
    )


@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    result = []
    for cid, msgs in conversations.items():
        result.append({
            "id": cid,
            "message_count": len(msgs),
            "preview": msgs[0]["content"][:80] if msgs else "",
        })
    return jsonify(result)


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({
        "id": conversation_id,
        "messages": conversations[conversation_id],
    })


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    if conversation_id in conversations:
        del conversations[conversation_id]
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    host = config["server"]["host"]
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    print(f"""
    ╔══════════════════════════════════════════╗
    ║          MIMI — Open Claw Agent          ║
    ║     Neon lights and clean code.          ║
    ╠══════════════════════════════════════════╣
    ║  Status:  ONLINE                         ║
    ║  Port:    {port:<30} ║
    ║  Mode:    {'DEBUG' if debug else 'PRODUCTION':<30} ║
    ║  API Key: {'SET' if os.environ.get('ANTHROPIC_API_KEY') else 'NOT SET (offline mode)':<30} ║
    ╚══════════════════════════════════════════╝
    """)

    app.run(host=host, port=port, debug=debug)
