#!/usr/bin/env python3
"""
start_railway.py — Railway launcher
Runs Flask web service (background thread) + Telegram bot (main thread).
Telegram's run_polling() requires the main thread for signal handlers.
"""

import os
import sys
import time
import traceback
import threading


def run_flask():
    """Start the Flask web service in a background thread."""
    try:
        port = int(os.environ.get("PORT", 8000))
        print(f"[Flask] Importing app...", flush=True)
        from app import app
        print(f"[Flask] Starting on port {port}...", flush=True)
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[Flask] FATAL: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    # Start Flask in a background thread (doesn't need signal handlers)
    port = os.environ.get("PORT", 8000)
    print(f"[start_railway] Starting Flask on port {port} (background thread)...", flush=True)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to start before Telegram bot takes over main thread
    time.sleep(2)

    # Run Telegram bot on the main thread (needs signal handlers)
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if tg_token:
        print("[start_railway] Starting Telegram bot on main thread...", flush=True)
        from telegram_bot import main as tg_main
        tg_main()  # Blocks forever (run_polling)
    else:
        print("[start_railway] No TELEGRAM_BOT_TOKEN set, keeping Flask alive...", flush=True)
        flask_thread.join()  # Block main thread so Flask stays up
