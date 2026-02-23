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

if __name__ == "__main__":
    print("[start_railway] v2 — 2026-02-23", flush=True)
    port = int(os.environ.get("PORT", 8000))

    # Import app on main thread FIRST to avoid import race conditions
    print(f"[start_railway] Importing app module...", flush=True)
    try:
        from app import (
            app, GOOGLE_AVAILABLE, TWILIO_AVAILABLE, TELEGRAM_OUTBOUND_AVAILABLE,
            GITHUB_AVAILABLE, TOOL_HANDLERS, CUSTOM_TOOLS, CUSTOM_AGENTS,
        )
        print(f"[start_railway] App imported OK", flush=True)
        print(f"[start_railway] Google: {'ON' if GOOGLE_AVAILABLE else 'OFF'}", flush=True)
        print(f"[start_railway] Twilio SMS: {'ON' if TWILIO_AVAILABLE else 'OFF'}", flush=True)
        print(f"[start_railway] Telegram outbound: {'ON' if TELEGRAM_OUTBOUND_AVAILABLE else 'OFF'}", flush=True)
        print(f"[start_railway] GitHub: {'ON' if GITHUB_AVAILABLE else 'OFF'}", flush=True)
        print(f"[start_railway] Custom tools: {len(CUSTOM_TOOLS)}", flush=True)
        print(f"[start_railway] Custom agents: {len(CUSTOM_AGENTS)}", flush=True)
        print(f"[start_railway] Total tools: {len(TOOL_HANDLERS)}", flush=True)
        print(f"[start_railway] Tool names: {sorted(TOOL_HANDLERS.keys())}", flush=True)
    except Exception as e:
        print(f"[start_railway] FATAL: Failed to import app: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    # Start Flask in a background thread
    def run_flask():
        try:
            print(f"[Flask] Starting on 0.0.0.0:{port}...", flush=True)
            app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        except Exception as e:
            print(f"[Flask] FATAL: {e}", file=sys.stderr, flush=True)
            traceback.print_exc()

    print(f"[start_railway] Launching Flask thread on port {port}...", flush=True)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to bind the port
    time.sleep(1)

    # Run Telegram bot on the main thread (needs signal handlers)
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if tg_token:
        print("[start_railway] Starting Telegram bot on main thread...", flush=True)
        from telegram_bot import main as tg_main
        tg_main()  # Blocks forever (run_polling)
    else:
        print("[start_railway] No TELEGRAM_BOT_TOKEN set, keeping Flask alive...", flush=True)
        flask_thread.join()
