#!/usr/bin/env bash
set -e

echo "🏭 Agent Factory Platform"
echo "Python: $(python3 --version)"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet || true

# Create data directory
mkdir -p data

# Check for at least one API key
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$XAI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: No LLM API key found!"
    echo "   Set ANTHROPIC_API_KEY, XAI_API_KEY, or OPENAI_API_KEY"
fi

PORT="${PORT:-8000}"
echo "🚀 Starting Agent Factory on http://0.0.0.0:${PORT}"
echo "📚 API Docs: http://0.0.0.0:${PORT}/api/docs"
exec uvicorn agent_factory_server:app --host 0.0.0.0 --port "$PORT"
