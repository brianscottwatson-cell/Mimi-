#!/usr/bin/env python3
"""
start_railway.py — Railway launcher
Runs both the Flask web service (on $PORT) and the Telegram bot in a background thread.
"""

import os
import sys
import threading


def run_telegram_bot():
    """Start the Telegram bot in a background thread."""
    try:
        # Import here to avoid blocking Flask startup if Telegram config is missing
        from telegram_bot import main as tg_main
        tg_main()
    except Exception as e:
        print(f"[start_railway] Telegram bot failed: {e}", file=sys.stderr)


def run_flask():
    """Start the Flask/gunicorn web service."""
    port = int(os.environ.get("PORT", 8000))

    # Try gunicorn first (production), fall back to Flask dev server
    try:
        from gunicorn.app.wsgiapp import WSGIApplication

        sys.argv = [
            "gunicorn",
            "app:app",
            "--bind", f"0.0.0.0:{port}",
            "--workers", "2",
            "--timeout", "120",
            "--access-logfile", "-",
        ]
        WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]").run()
    except ImportError:
        print("[start_railway] gunicorn not found, using Flask dev server")
        from app import app
        app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Start Telegram bot in a daemon thread (won't block shutdown)
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if tg_token:
        print("[start_railway] Starting Telegram bot in background thread...")
        tg_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        tg_thread.start()
    else:
        print("[start_railway] No TELEGRAM_BOT_TOKEN set, skipping Telegram bot.")

    # Start Flask web service (blocking)
    print(f"[start_railway] Starting Flask on port {os.environ.get('PORT', 8000)}...")
    run_flask()
