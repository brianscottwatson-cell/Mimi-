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
        from api_server import start_server
        port = int(os.getenv("PORT", 8000))
        start_server(port=port)

    elif mode == "terminal":
        print("💻 Starting Terminal Interface...")
        from terminal_interface import main as terminal_main
        terminal_main()

    else:
        print(f"❌ Unknown mode: {mode}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
