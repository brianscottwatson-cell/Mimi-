#!/usr/bin/env bash
set -e

echo "Starting Mimi agent..."
echo "Python version: $(python3 --version)"

pip install -r requirements.txt || true

exec python3 main.py