# Claudebot Setup & Run

## 1. Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org))
- **PostgreSQL** 12+ ([download](https://www.postgresql.org) or use Docker)
- **Anthropic API key** ([get one](https://console.anthropic.com))

## 2. Database Setup (macOS)

```bash
# Install PostgreSQL with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb claudebot

# Verify connection
psql -l
```

**Or use Docker:**

```bash
docker run -d \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=claudebot \
  -p 5432:5432 \
  postgres:15
```

## 3. Project Setup

```bash
cd claudebot

# Install dependencies
npm install

# Create .env file (copy from .env.example)
cp .env.example .env

# Edit .env and add:
# - DATABASE_URL (adjust for your PostgreSQL setup)
# - ANTHROPIC_API_KEY
```

### Example .env

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/claudebot
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
PORT=3000
```

## 4. Initialize Database

```bash
npm run db:push
```

This creates the tables: `configs`, `conversations`, `messages`

## 5. Start Development

### Web + API Server

```bash
npm run dev
```

Open browser: **http://localhost:3000**

### CLI (in another terminal)

```bash
npm run cli
```

## Features

✅ Web chat interface (React + cyberpunk theme)
✅ CLI chat (terminal)
✅ Real-time WebSocket support
✅ Persistent conversation history
✅ Claude 3.5 Sonnet AI

## Troubleshooting

**"Cannot find module 'pg'"**
→ Run `npm install`

**"DATABASE_URL must be set"**
→ Check your `.env` file has `DATABASE_URL`

**"Connection refused"**
→ PostgreSQL not running. Run `brew services start postgresql@15`

**Port 3000 already in use**
→ Set `PORT=3001 npm run dev`

## Next Steps

- Add file upload support
- Integrate ElevenLabs voice
- Deploy to cloud (Vercel/Railway/Replit)
- Add more AI providers (Grok, Moonshot, etc.)
