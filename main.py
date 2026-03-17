#!/usr/bin/env python3
"""
Multi-Agent AI System
Entry point for both terminal and web interfaces.
"""
import sys
import os


def print_usage():
    """Print usage information."""
    print("""
Multi-Agent AI System - Main Entry Point

Usage:
  python main.py [mode]

Modes:
  web       - Start web server (default for deployment)
  terminal  - Start terminal interface (default for local use)
  help      - Show this help message

Examples:
  python main.py              # Auto-select based on environment
  python main.py web          # Start web server
  python main.py terminal     # Start terminal interface

Environment Variables:
  ANTHROPIC_API_KEY - Your Anthropic API key (required for Claude)
  KIMI_API_KEY      - Your Kimi API key (optional, for Kimi K2)
  PORT              - Port for web server (default: 8000)
""")


def main():
    """Main entry point."""
    # Get mode from command line or environment
    mode = None

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    if mode == "help":
        print_usage()
        return

    # Auto-detect mode if not specified
    if mode is None:
        # If PORT is set (Railway/Heroku), default to web
        # Otherwise, default to terminal for local use
        if os.getenv("PORT"):
            mode = "web"
        else:
            mode = "terminal"

    # Launch appropriate interface
    if mode == "web":
        print("🌐 Starting Web Server...")
        # Add server directory to path so imports work
        server_dir = os.path.join(os.path.dirname(__file__), "claudebot", "web", "server")
        sys.path.insert(0, server_dir)

        # Initialize persistent memory
        try:
            from memory import init_db
            init_db()
            print("Persistent memory initialized (SQLite)")
        except Exception as e:
            print(f"WARNING: Memory init failed: {e}")

        from app import app
        port = int(os.getenv("PORT", 8000))
        print(f"Mimi Gateway — Model loaded, port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)

    elif mode == "terminal":
        print("💻 Starting Terminal Interface...")
        server_dir = os.path.join(os.path.dirname(__file__), "claudebot", "web", "server")
        sys.path.insert(0, server_dir)
        from app import app
        port = int(os.getenv("PORT", 8000))
        app.run(host="0.0.0.0", port=port, debug=True)

    else:
        print(f"❌ Unknown mode: {mode}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
