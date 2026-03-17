#!/usr/bin/env python3
"""
telegram_bot.py — Mimi on Telegram (v2)
Upgrades: webhook mode, persistent memory, streaming responses,
conversation summarization, x.ai image generation, extended thinking.
Uses python-telegram-bot v20+ (async).
"""

import os
import io
import logging
from collections import defaultdict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import json as _json
import anthropic

from mimi_core import (
    SYSTEM_PROMPT, MODEL, IMAGE_TYPES,
    async_client,
    achat_with_mimi,
    process_image_bytes, process_document_bytes,
    tts_to_ogg_bytes, XAI_API_KEY,
    asummarize_conversation, build_messages_with_summary,
    SUMMARIZE_THRESHOLD, KEEP_RECENT,
    axai_generate_image,
    _needs_thinking, THINKING_BUDGET,
)

from memory import (
    save_message, get_history, clear_history,
    get_message_count, save_summary, get_latest_summary,
    get_preference, set_preference,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()  # e.g. https://your-app.railway.app

# Optional comma-separated user IDs to restrict access
_allowed_raw = os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
ALLOWED_USERS: set[int] | None = (
    {int(uid.strip()) for uid in _allowed_raw.split(",") if uid.strip()}
    if _allowed_raw else None
)

MAX_HISTORY = 50          # max messages to load from DB per turn
TELEGRAM_MSG_LIMIT = 4096  # Telegram text message char limit

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("mimi-telegram")

# ---------------------------------------------------------------------------
# Per-user in-memory state (supplements persistent DB)
# ---------------------------------------------------------------------------

# voice mode toggle: user_id -> bool
user_voice: dict[int, bool] = defaultdict(bool)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_allowed(user_id: int) -> bool:
    return ALLOWED_USERS is None or user_id in ALLOWED_USERS


def _split_message(text: str, limit: int = TELEGRAM_MSG_LIMIT) -> list[str]:
    """Split long text into chunks that fit Telegram's char limit."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


async def _get_messages_with_context(uid: int) -> list[dict]:
    """Load conversation history with smart summarization."""
    history = get_history("telegram", str(uid), limit=MAX_HISTORY)
    msg_count = get_message_count("telegram", str(uid))

    if msg_count > SUMMARIZE_THRESHOLD:
        # Check if we have a recent summary
        existing_summary = get_latest_summary("telegram", str(uid))
        summary_text = None

        if existing_summary and existing_summary["messages_covered"] >= msg_count - KEEP_RECENT - 10:
            # Summary is recent enough
            summary_text = existing_summary["summary"]
        elif len(history) > KEEP_RECENT:
            # Generate new summary from older messages
            old_messages = history[:-KEEP_RECENT]
            summary_text = await asummarize_conversation(old_messages)
            if summary_text:
                save_summary("telegram", str(uid), summary_text, msg_count - KEEP_RECENT)

        return build_messages_with_summary(history, summary_text)

    return history


# ---------------------------------------------------------------------------
# Async tool-calling chat with streaming + extended thinking
# ---------------------------------------------------------------------------

from app import (
    WEB_TOOLS, GOOGLE_TOOLS, GOOGLE_AVAILABLE,
    DASHBOARD_TOOLS, GITHUB_TOOLS, GITHUB_AVAILABLE,
    TOOL_HANDLERS,
)

# Image generation tool definition
IMAGE_GEN_TOOL = {
    "name": "generate_image",
    "description": "Generate an image using x.ai's Grok image model. Use when Brian asks to create, visualize, design, or imagine something visual. [Dax] should use this for visual concepts. Enhance the prompt with rich detail for better results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Detailed image generation prompt. Be specific about style, colors, composition, subjects, mood, and artistic direction.",
            },
            "n": {
                "type": "integer",
                "description": "Number of images to generate (1-4, default 1)",
                "default": 1,
            },
        },
        "required": ["prompt"],
    },
}


async def _achat_with_tools(messages: list[dict], stream_callback=None) -> str:
    """Async chat with full tool access, streaming, extended thinking, and image gen."""
    tools = list(WEB_TOOLS)
    if GOOGLE_AVAILABLE:
        tools.extend(GOOGLE_TOOLS)
    tools.extend(DASHBOARD_TOOLS)
    if GITHUB_AVAILABLE:
        tools.extend(GITHUB_TOOLS)
    if XAI_API_KEY:
        tools.append(IMAGE_GEN_TOOL)

    # Check if extended thinking should be enabled
    use_thinking = _needs_thinking(messages)
    kwargs = dict(
        model=MODEL,
        max_tokens=THINKING_BUDGET + 4096 if use_thinking else 4096,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=tools if tools else anthropic.NOT_GIVEN,
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": THINKING_BUDGET}

    if stream_callback:
        # Streaming mode
        response_text = ""
        async with async_client.messages.stream(**kwargs) as stream:
            response = await stream.get_final_message()
    else:
        response = await async_client.messages.create(**kwargs)

    for _ in range(5):
        if response.stop_reason != "tool_use":
            break

        assistant_content = response.content
        tool_results = []

        for block in assistant_content:
            if block.type == "tool_use":
                # Handle image generation specially
                if block.name == "generate_image":
                    try:
                        result = await axai_generate_image(**block.input)
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
                    continue

                handler = TOOL_HANDLERS.get(block.name)
                if handler:
                    try:
                        result = handler(**block.input)
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
                        "content": f"Tool '{block.name}' not available.",
                        "is_error": True,
                    })

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        # Subsequent calls don't need thinking (already thought about it)
        follow_kwargs = dict(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )
        response = await async_client.messages.create(**follow_kwargs)

    # Extract text, skipping thinking blocks
    text_parts = [b.text for b in response.content if hasattr(b, "text") and b.type == "text"]
    return "\n".join(text_parts) if text_parts else "Done."


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update.effective_user.id):
        await update.message.reply_text("Access restricted.")
        return
    await update.message.reply_text(
        "Hey Brian — Mimi here, plugged into Telegram.\n"
        "Send me a message, photo, or doc and I'll handle it.\n\n"
        "Commands:\n"
        "/clear — reset conversation\n"
        "/voice — toggle voice note replies\n"
        "/imagine <prompt> — generate an image\n"
        "/status — check my capabilities"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    clear_history("telegram", str(uid))
    await update.message.reply_text("History cleared. Fresh start.")


async def cmd_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    user_voice[uid] = not user_voice[uid]
    set_preference("telegram", str(uid), "voice", str(user_voice[uid]))
    status = "ON" if user_voice[uid] else "OFF"
    extra = "" if XAI_API_KEY else " (Note: XAI_API_KEY not set — voice won't work until configured)"
    await update.message.reply_text(f"Voice replies: {status}{extra}")


async def cmd_imagine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Direct image generation command: /imagine <prompt>"""
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    prompt = " ".join(context.args) if context.args else ""
    if not prompt:
        await update.message.reply_text("Usage: /imagine <description of the image you want>")
        return

    await update.message.reply_text("[Dax] Generating your image...")

    result = await axai_generate_image(prompt)
    if "error" in result:
        await update.message.reply_text(f"Image generation failed: {result['error']}")
        return

    for img in result.get("images", []):
        if img.get("url"):
            await update.message.reply_photo(photo=img["url"], caption=f"[Dax] {prompt[:200]}")
        elif img.get("b64_json"):
            import base64
            img_bytes = base64.b64decode(img["b64_json"])
            await update.message.reply_photo(photo=io.BytesIO(img_bytes), caption=f"[Dax] {prompt[:200]}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current capabilities and status."""
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    msg_count = get_message_count("telegram", str(uid))
    voice_on = user_voice.get(uid, False)

    status_lines = [
        f"**Mimi Status**",
        f"Model: {MODEL}",
        f"Extended Thinking: enabled",
        f"Persistent Memory: {msg_count} messages stored",
        f"Voice: {'ON' if voice_on else 'OFF'}",
        f"Image Gen (x.ai): {'ready' if XAI_API_KEY else 'not configured'}",
        f"Google Services: {'connected' if GOOGLE_AVAILABLE else 'not connected'}",
        f"GitHub: {'connected' if GITHUB_AVAILABLE else 'not connected'}",
        f"Web Search: ready",
    ]
    await update.message.reply_text("\n".join(status_lines))


# ---------------------------------------------------------------------------
# Message handlers
# ---------------------------------------------------------------------------

async def _reply_to_user(update: Update, text: str, uid: int) -> None:
    """Send text reply, optionally with a voice note. Handle image URLs."""
    # Check if response contains image URLs from generate_image tool
    # Send text chunks
    for chunk in _split_message(text):
        await update.message.reply_text(chunk)

    # Send voice note if enabled
    if user_voice.get(uid) and XAI_API_KEY:
        try:
            ogg_bytes = await tts_to_ogg_bytes(text)
            if ogg_bytes:
                await update.message.reply_voice(voice=io.BytesIO(ogg_bytes))
        except Exception as exc:
            logger.warning("TTS failed for user %s: %s", uid, exc)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    user_text = update.message.text or ""
    if not user_text.strip():
        return

    # Save to persistent memory
    save_message("telegram", str(uid), "user", user_text)

    # Load history with smart summarization
    messages = await _get_messages_with_context(uid)

    # Send typing indicator
    await update.message.chat.send_action("typing")

    try:
        reply = await _achat_with_tools(list(messages))
    except Exception as e:
        logger.error("Chat error for user %s: %s", uid, e)
        reply = f"[LINK ERROR] Something went sideways: {e}"

    # Save assistant reply to persistent memory
    save_message("telegram", str(uid), "assistant", reply)

    await _reply_to_user(update, reply, uid)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    data = await file.download_as_bytearray()

    caption = update.message.caption or "What do you see in this image?"

    image_block = process_image_bytes(bytes(data), "image/jpeg", "photo.jpg")
    content = [image_block, {"type": "text", "text": caption}]

    # Save to persistent memory (just the text part)
    save_message("telegram", str(uid), "user", f"[Photo] {caption}")

    messages = await _get_messages_with_context(uid)
    # Replace last message content with the full image+text content
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] = content

    await update.message.chat.send_action("typing")

    try:
        reply = await _achat_with_tools(list(messages))
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    save_message("telegram", str(uid), "assistant", reply)
    await _reply_to_user(update, reply, uid)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    filename = doc.file_name or "file"
    mime = doc.mime_type or ""

    caption = update.message.caption or f"Please analyze this file: {filename}"

    if mime in IMAGE_TYPES:
        image_block = process_image_bytes(bytes(data), mime, filename)
        content = [image_block, {"type": "text", "text": caption}]
    else:
        block = process_document_bytes(bytes(data), filename)
        if block:
            content = [block, {"type": "text", "text": caption}]
        else:
            await update.message.reply_text(f"Can't read that file type ({mime or 'unknown'}). Try a text-based file or image.")
            return

    save_message("telegram", str(uid), "user", f"[Document: {filename}] {caption}")

    messages = await _get_messages_with_context(uid)
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] = content

    await update.message.chat.send_action("typing")

    try:
        reply = await _achat_with_tools(list(messages))
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    save_message("telegram", str(uid), "assistant", reply)
    await _reply_to_user(update, reply, uid)

# ---------------------------------------------------------------------------
# Main — supports both polling and webhook modes
# ---------------------------------------------------------------------------

def _build_app() -> Application:
    """Build the telegram Application with all handlers."""
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set.")
        raise SystemExit(1)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("voice", cmd_voice))
    app.add_handler(CommandHandler("imagine", cmd_imagine))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    return app


def main() -> None:
    """Start the bot — webhook if TELEGRAM_WEBHOOK_URL is set, polling otherwise."""
    print(f"Mimi Telegram Bot — Model: {MODEL}")
    print(f"Allowed users: {ALLOWED_USERS or 'everyone'}")
    print(f"Voice (x.ai): {'configured' if XAI_API_KEY else 'not configured'}")
    print(f"Image gen (x.ai): {'configured' if XAI_API_KEY else 'not configured'}")
    print(f"Persistent memory: enabled (SQLite)")

    app = _build_app()

    if WEBHOOK_URL:
        # Webhook mode — faster, more reliable, less resource usage
        port = int(os.environ.get("TELEGRAM_WEBHOOK_PORT", os.environ.get("PORT", "8443")))
        webhook_path = "/telegram/webhook"
        full_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"

        print(f"Starting webhook on port {port}")
        print(f"Webhook URL: {full_url}")

        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=full_url,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Polling mode (fallback for local dev)
        print("Polling for messages...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
