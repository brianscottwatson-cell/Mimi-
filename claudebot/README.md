# Claudebot

A cyberpunk-styled AI assistant with web and CLI interfaces. Built with Node.js, React, and Claude 3.5 Sonnet.

## Features

- 💻 **Web Interface** – Cyberpunk dashboard accessible on desktop & mobile
- 🖥️ **CLI Mode** – Terminal-based interactive chat with code execution
- 💬 **Real-time Chat** – WebSocket support for instant messaging
- 📁 **File Upload & Analysis** – Images, PDFs, text, CSV, audio, video
- 🎙️ **Voice (TTS/STT)** – ElevenLabs text-to-speech and speech recognition
- 🔧 **Code Execution** – Run JavaScript, Python, Bash directly from chat
- 💾 **Persistent History** – All conversations saved to PostgreSQL
- 🔄 **Extensible API** – Easy to add more AI providers and integrations

## Prerequisites

- Node.js 18+
- PostgreSQL 12+
- Anthropic API key

## Quick Start

**See [QUICKSTART.md](QUICKSTART.md) for fastest setup (Docker or Railway).**

### Local Development

**1. Setup PostgreSQL**

```bash
# macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Or use Docker
docker run -d -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
```

**2. Create Database**

```bash
createdb claudebot
```

**3. Install Dependencies**

```bash
cd claudebot
npm install
```

**4. Configure Environment**

Create `.env`:

```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/claudebot
ANTHROPIC_API_KEY=sk-ant-...
PORT=3000
```

**5. Set Up Database Schema**

```bash
npm run db:push
```

**6. Run Development Server**

```bash
npm run dev
```

Visit `http://localhost:3000` in your browser.

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for:
- Docker (local or any cloud)
- Railway.app (recommended, easiest)
- Render (alternative cloud option)
- Vercel (frontend only)
- Scaling & production tips
- Security best practices

## CLI Usage

In a separate terminal:

```bash
npm run cli
```

Type messages, type `exit` to quit.

## Project Structure

```
claudebot/
├── client/               # React frontend
│   └── src/
│       ├── App.tsx       # Main app
│       ├── pages/
│       │   └── Chat.tsx  # Chat interface
│       └── index.css     # Tailwind + cyberpunk theme
├── server/               # Express backend
│   ├── index.ts          # Server entry point
│   ├── claude.ts         # Anthropic API integration
│   ├── storage.ts        # Database CRUD
│   └── db.ts             # Drizzle ORM setup
├── cli/                  # CLI interface
│   └── index.ts          # CLI entry point
├── shared/               # Shared types
│   └── schema.ts         # Database schema
└── package.json
```

## API Endpoints

- `GET /api/conversations` – List conversations
- `POST /api/conversations` – Create conversation
- `GET /api/conversations/:id/messages` – Get messages
- `POST /api/conversations/:id/messages` – Send message
- `POST /api/files/upload` – Upload and analyze files
- `CLI Commands

In terminal mode (`npm run cli`):

```
/exec <code>   - Execute JavaScript code
/py <code>     - Execute Python code
/help          - Show available commands
/quit          - Exit CLI
```

Example:
```
You: /exec console.log("Hello from JS!")
✓ Output:
Hello from JS!

You: /py print(sum([1, 2, 3, 4, 5]))
✓ Output:
15 "..." }

// Server → Client
{ "type": "message", "data": { ... } }
{ "type": "error", "message": "..." }
```

## Development

Watch for changes:

```bash
npm run dev
```

Build for production:

```bash
npm run build
npm start
```

## Database Management

View/edit schema:

```bash
npm run db:studio
```

## License

MIT
