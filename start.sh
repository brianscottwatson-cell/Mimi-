#!/usr/bin/env bash
set -e

echo "Starting Mimi agent..."
echo "Python version: $(python3 --version)"

# Install dependencies (Railpack may already do this, but safe)
pip install -r requirements.txt || true

# Run your main script
exec python3 main.py
