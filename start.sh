#!/usr/bin/env bash
set -e

echo "Starting Mimi agent..."
echo "Python version: $(python --version)"

pip install -r requirements.txt || true

exec python main.py
