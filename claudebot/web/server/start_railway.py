#!/usr/bin/env python3
"""
start_railway.py — Railway launcher (v2)
Runs Flask web service (background thread) + Telegram bot (main thread).
Supports both polling and webhook modes for Telegram.

If TELEGRAM_WEBHOOK_URL is set, uses webhook mode (faster, more reliable).
Otherwise, falls back to polling mode.
"""

import os
import sys
import time
import traceback
import threading

# Ensure the server directory is on sys.path so relative imports work
# regardless of the working directory
_server_dir = os.path.dirname(os.path.abspath(__file__))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

if __name__ == "__main__":
    print("[start_railway] v2 — 2026-02-23", flush=True)
    port = int(os.environ.get("PORT", 8000))
    webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL", "").strip()

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

    # Initialize persistent memory
    try:
        from memory import init_db
        init_db()
        print("[start_railway] Persistent memory initialized (SQLite)", flush=True)
    except Exception as e:
        print(f"[start_railway] WARNING: Memory init failed: {e}", flush=True)

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
        if webhook_url:
            print(f"[start_railway] Starting Telegram bot in WEBHOOK mode...", flush=True)
            print(f"[start_railway] Webhook URL: {webhook_url}", flush=True)
            # In webhook mode, Telegram updates come through Flask
            # We just need to set up the webhook and keep Flask alive
            from telegram_bot import _build_app
            import asyncio

            async def setup_webhook():
                tg_app = _build_app()
                webhook_path = "/telegram/webhook"
                full_url = f"{webhook_url.rstrip('/')}{webhook_path}"

                await tg_app.initialize()
                await tg_app.bot.set_webhook(url=full_url, allowed_updates=["message"])
                print(f"[start_railway] Webhook set: {full_url}", flush=True)

                # Add webhook handler to Flask
                from telegram import Update as TgUpdate

                @app.route(webhook_path, methods=["POST"])
                def telegram_webhook():
                    """Handle incoming Telegram webhook updates."""
                    from flask import request
                    update = TgUpdate.de_json(request.get_json(force=True), tg_app.bot)
                    # Process update asynchronously
                    asyncio.run_coroutine_threadsafe(
                        tg_app.process_update(update),
                        loop
                    )
                    return "ok", 200

                await tg_app.start()
                return tg_app

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tg_app = loop.run_until_complete(setup_webhook())

            # Keep the event loop running for processing updates
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                loop.run_until_complete(tg_app.stop())
                loop.close()
        else:
            print("[start_railway] Starting Telegram bot in POLLING mode...", flush=True)
            from telegram_bot import main as tg_main
            tg_main()  # Blocks forever (run_polling)
    else:
        print("[start_railway] No TELEGRAM_BOT_TOKEN set, keeping Flask alive...", flush=True)
        flask_thread.join()
