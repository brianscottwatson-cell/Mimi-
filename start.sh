#!/usr/bin/env bash
set -e

echo "Starting Multi-Agent AI System..."
echo "Python version: $(python3 --version)"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt || true

# Check for API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$KIMI_API_KEY" ]; then
    echo "WARNING: No API keys found!"
    echo "Set ANTHROPIC_API_KEY or KIMI_API_KEY in your environment"
fi

# Start the application (pass any arguments through)
echo "Starting application..."
exec python3 main.py "$@"