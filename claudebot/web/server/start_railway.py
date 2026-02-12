#!/usr/bin/env python3
"""
start_railway.py — Railway launcher
Runs both the Flask web service (on $PORT) and the Telegram bot in a background thread.
"""

import os
import sys
import asyncio
import threading


def run_telegram_bot():
    """Start the Telegram bot in a background thread with its own event loop."""
    try:
        import importlib
        telegram_bot = importlib.import_module("telegram_bot")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        telegram_bot.main()
    except Exception as e:
        print(f"[start_railway] Telegram bot failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


def run_flask():
    """Start the Flask web service."""
    port = int(os.environ.get("PORT", 8000))

    # Use Flask dev server directly — gunicorn's forking model kills
    # the Telegram bot thread, so we avoid it for this combined launcher.
    from app import app
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    # Start Telegram bot in a daemon thread (won't block shutdown)
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if tg_token:
        print("[start_railway] Starting Telegram bot in background thread...")
        tg_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        tg_thread.start()
    else:
        print("[start_railway] No TELEGRAM_BOT_TOKEN set, skipping Telegram bot.")

    # Start Flask web service (blocking — must be on main thread)
    port = os.environ.get("PORT", 8000)
    print(f"[start_railway] Starting Flask on port {port}...")
    run_flask()
