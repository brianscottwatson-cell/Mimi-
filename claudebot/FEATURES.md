# Claudebot Features Guide

## Core Features

### 1. Web Chat Interface
- Real-time messaging with Claude 3.5 Sonnet
- Cyberpunk-themed UI with neon colors & scanlines
- Conversation history in sidebar
- Multi-device access (desktop + mobile)

**Access:** `http://localhost:3000`

### 2. CLI Chat
- Terminal-based interactive chat
- Same backend as web interface
- Local conversation storage
- Code execution commands

**Start:** `npm run cli`

### 3. File Upload & Analysis
- Upload images, PDFs, text files, CSV, audio, video
- Automatic file analysis and summarization
- Store file metadata with messages

**API:** `POST /api/files/upload`

### 4. Voice (ElevenLabs)
- Text-to-Speech (TTS) with multiple voices
- Speech-to-Text (STT) for voice input
- Real-time audio streaming

**Setup:** Set `ELEVENLABS_API_KEY` in `.env`

**Available voices:**
- Rachel, Bella, Antoni, Arnold, Domi

**API:** 
- `POST /api/voice/tts` – Convert text to audio
- `GET /api/voice/voices` – List available voices

### 5. Code Execution
Execute code directly from CLI or chat:

**JavaScript:**
```
/exec console.log("Hello World")
/exec const sum = (a, b) => a + b; sum(5, 3)
```

**Python:**
```
/py print("Hello World")
/py import math; print(math.pi)
```

**Bash:**
- Coming soon in web UI

**API:** `POST /api/execute`

Body:
```json
{
  "code": "console.log('test')",
  "language": "javascript"
}
```

### 6. Persistent Storage
- PostgreSQL database with Drizzle ORM
- Conversations table
- Messages table with role & content
- Config key-value store

**Tables:**
- `conversations` – Chat sessions
- `messages` – Individual messages
- `configs` – Key-value settings

## Usage Examples

### Web Chat
1. Open `http://localhost:3000`
2. Create new chat with "+ NEW CHAT" button
3. Type messages, press SEND
4. View entire conversation history

### CLI Chat
```bash
$ npm run cli

╔════════════════════════════════╗
║   CLAUDEBOT CLI - GATEWAY      ║
║   v1.0 | OPERATIONAL           ║
╚════════════════════════════════╝

Commands:
  /exec <code>   - Execute JavaScript
  /py <code>     - Execute Python
  /help          - Show this help
  /quit          - Exit

You: What is 5 + 5?
Claude: 5 + 5 equals 10.

You: /exec [1,2,3].reduce((a,b) => a+b, 0)
✓ Output:
6

You: /quit
Goodbye!
```

### File Upload (REST)
```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:3000/api/files/upload
```

Response:
```json
{
  "filename": "document.pdf",
  "mimetype": "application/pdf",
  "size": 256000,
  "analysis": "[PDF document: document.pdf]"
}
```

### Text-to-Speech
```bash
curl -X POST http://localhost:3000/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "voiceId": "21m00Tcm4TlvDq8ikWAM"}' \
  --output audio.mp3
```

### Code Execution
```bash
curl -X POST http://localhost:3000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "console.log(2 ** 10)",
    "language": "javascript"
  }'
```

Response:
```json
{
  "output": "1024",
  "error": null
}
```

## Security Notes

⚠️ **Code execution is sandboxed** with 5-second timeout and 10MB output limit.

⚠️ **File uploads** are limited to 50MB and only allow safe file types.

⚠️ **Never expose** ANTHROPIC_API_KEY or ELEVENLABS_API_KEY publicly.

## Roadmap

- [ ] Google Calendar integration
- [ ] Google Drive file browser
- [ ] Gmail integration
- [ ] Streaming responses
- [ ] Web UI for code execution
- [ ] Conversation export (JSON/PDF)
- [ ] Multi-model support (Grok, Claude 3 Opus, etc.)
- [ ] Docker deployment
- [ ] Mobile app (React Native)

## Troubleshooting

**"Cannot POST /api/execute"**
→ Make sure you're sending `Content-Type: application/json`

**Voice features not working**
→ Set `ELEVENLABS_API_KEY` in `.env` and restart server

**Code execution timeout**
→ Code is limited to 5 seconds. Infinite loops will fail.

**File upload fails**
→ Check file size < 50MB and type is supported

For more help, see [SETUP.md](SETUP.md).
