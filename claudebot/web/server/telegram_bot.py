#!/usr/bin/env python3
"""
telegram_bot.py — Mimi on Telegram
Uses python-telegram-bot v20+ (async) with polling.
Run directly: python web/server/telegram_bot.py
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

from mimi_core import (
    SYSTEM_PROMPT, MODEL, IMAGE_TYPES,
    achat_with_mimi,
    process_image_bytes, process_document_bytes,
    tts_to_ogg_bytes, XAI_API_KEY,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Optional comma-separated user IDs to restrict access
_allowed_raw = os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
ALLOWED_USERS: set[int] | None = (
    {int(uid.strip()) for uid in _allowed_raw.split(",") if uid.strip()}
    if _allowed_raw else None
)

MAX_HISTORY = 50          # max messages per user
TELEGRAM_MSG_LIMIT = 4096  # Telegram text message char limit

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("mimi-telegram")

# ---------------------------------------------------------------------------
# Per-user state
# ---------------------------------------------------------------------------

# conversation history: user_id -> list of {role, content} dicts
user_histories: dict[int, list[dict]] = defaultdict(list)

# voice mode toggle: user_id -> bool
user_voice: dict[int, bool] = defaultdict(bool)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_allowed(user_id: int) -> bool:
    """Check if user is allowed (None = everyone allowed)."""
    return ALLOWED_USERS is None or user_id in ALLOWED_USERS


def _trim_history(user_id: int) -> None:
    """Keep history under MAX_HISTORY messages."""
    hist = user_histories[user_id]
    if len(hist) > MAX_HISTORY:
        user_histories[user_id] = hist[-MAX_HISTORY:]


def _split_message(text: str, limit: int = TELEGRAM_MSG_LIMIT) -> list[str]:
    """Split long text into chunks that fit Telegram's char limit."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        # Try to split on newline
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            # Fall back to space
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks

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
        "/voice — toggle voice note replies"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    user_histories[uid].clear()
    await update.message.reply_text("History cleared. Fresh start.")


async def cmd_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    user_voice[uid] = not user_voice[uid]
    status = "ON" if user_voice[uid] else "OFF"
    extra = "" if XAI_API_KEY else " (Note: XAI_API_KEY not set — voice won't work until configured)"
    await update.message.reply_text(f"Voice replies: {status}{extra}")

# ---------------------------------------------------------------------------
# Message handlers
# ---------------------------------------------------------------------------

async def _reply_to_user(update: Update, text: str, uid: int) -> None:
    """Send text reply, optionally with a voice note."""
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

    hist = user_histories[uid]
    hist.append({"role": "user", "content": user_text})
    _trim_history(uid)

    try:
        reply = await achat_with_mimi(hist)
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    hist.append({"role": "assistant", "content": reply})
    _trim_history(uid)

    await _reply_to_user(update, reply, uid)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    # Get largest photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    data = await file.download_as_bytearray()

    caption = update.message.caption or "What do you see in this image?"

    image_block = process_image_bytes(bytes(data), "image/jpeg", "photo.jpg")
    content = [image_block, {"type": "text", "text": caption}]

    hist = user_histories[uid]
    hist.append({"role": "user", "content": content})
    _trim_history(uid)

    try:
        reply = await achat_with_mimi(hist)
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    hist.append({"role": "assistant", "content": reply})
    _trim_history(uid)

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

    # Check if it's an image sent as document
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

    hist = user_histories[uid]
    hist.append({"role": "user", "content": content})
    _trim_history(uid)

    try:
        reply = await achat_with_mimi(hist)
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    hist.append({"role": "assistant", "content": reply})
    _trim_history(uid)

    await _reply_to_user(update, reply, uid)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set. Add it to .env or environment variables.")
        raise SystemExit(1)

    print(f"Mimi Telegram Bot — Model: {MODEL}")
    print(f"Allowed users: {ALLOWED_USERS or 'everyone'}")
    print(f"Voice (x.ai): {'configured' if XAI_API_KEY else 'not configured'}")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("voice", cmd_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Polling for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
