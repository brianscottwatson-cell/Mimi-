# Multi-Agent AI System 🤖

A sophisticated multi-agent AI system with a primary orchestrator and specialized sub-agents for different domains. Accessible from both your computer (terminal) and phone (web browser).

## Features ✨

- **Primary Orchestrator Agent**: Intelligently routes tasks to specialized agents
- **Specialized Agents**:
  - 🔍 Research Specialist
  - 📢 Marketing Specialist
  - 🔎 SEO Specialist
  - 💻 Digital Marketing Specialist
  - 📋 Project Management Specialist
  - 🌐 Web Development Specialist
- **Dual Interface**: Terminal (computer) + Web UI (phone/browser)
- **Model Flexibility**: Switch between Claude Sonnet 4.5 and Kimi K2
- **Tool Integration**: Web search, code execution, file operations, web scraping
- **Session Management**: Persistent conversations per session

## Quick Start 🚀

### 1. Setup

```bash
# Clone or navigate to the project
cd anthropic-test

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your API key(s)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (and optionally KIMI_API_KEY)
```

### 2. Get API Keys

You need at least one API key:

- **Anthropic (Claude)**: Get it from [console.anthropic.com](https://console.anthropic.com/)
- **Kimi (optional)**: Get it from [platform.moonshot.cn](https://platform.moonshot.cn/)

Add to your `.env` file:
```bash
ANTHROPIC_API_KEY=your_key_here
```

Or export directly:
```bash
export ANTHROPIC_API_KEY='your_key_here'
```

### 3. Run

#### Terminal Interface (Computer)
```bash
python main.py terminal
# or just
python main.py
```

#### Web Interface (Phone/Browser)
```bash
python main.py web
```

Then open your browser to `http://localhost:8000`

Or use the convenience script:
```bash
./start.sh terminal  # for terminal
./start.sh web       # for web server
```

## Usage Examples 💡

### Terminal Interface

```bash
$ python main.py terminal

You: Research the latest trends in AI for 2026

[research specialist]
Based on my research, here are the key AI trends for 2026:
1. Multimodal AI systems...
2. AI agents with tool use...
...

You: Create an SEO strategy for my e-commerce site

[seo specialist]
Here's a comprehensive SEO strategy for your e-commerce site...

You: status
System Status:
  Model Provider: anthropic
  Model Name: claude-sonnet-4-20250514
  Primary Agent: Primary Orchestrator
  Conversation Length: 4 messages
  Active Specialists:
    ● research: 2 messages
    ● seo: 2 messages
```

### Web Interface

Start the web server:
```bash
python main.py web
```

Access from:
- **Computer**: `http://localhost:8000`
- **Phone** (on same network): `http://[your-computer-ip]:8000`

The web interface provides a clean, mobile-friendly chat UI.

## Architecture 🏗️

```
┌─────────────────────────────────────┐
│      User (Terminal or Web)         │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│     Primary Orchestrator Agent      │
│  - Routes tasks to specialists      │
│  - Handles general queries          │
│  - Synthesizes responses            │
└─────────────┬───────────────────────┘
              │
              ▼
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
┌──────────┐      ┌──────────┐
│ Research │      │ Marketing│
│  Agent   │      │  Agent   │
└──────────┘      └──────────┘
    │                    │
    ▼                    ▼
┌──────────┐      ┌──────────┐
│   SEO    │      │ Digital  │
│  Agent   │      │Marketing │
└──────────┘      └──────────┘
    │                    │
    ▼                    ▼
┌──────────┐      ┌──────────┐
│ Project  │      │   Web    │
│Management│      │  Dev     │
└──────────┘      └──────────┘
```

## API Endpoints 📡

When running in web mode, the following endpoints are available:

- `GET /` - Web UI
- `POST /api/chat` - Send a message
  ```json
  {
    "message": "Your question here",
    "session_id": "optional-session-id"
  }
  ```
- `GET /api/status` - Get system status
- `GET /api/agents` - List available agents
- `POST /api/model/switch` - Switch AI model
  ```json
  {
    "model_provider": "anthropic",  // or "kimi"
    "model_name": "claude-sonnet-4-20250514"  // optional
  }
  ```
- `POST /api/reset?session_id=default` - Reset conversation
- `GET /health` - Health check

## Deployment 🚀

### Railway

1. Create a new project on [Railway](https://railway.app/)
2. Connect your GitHub repository
3. Add environment variable: `ANTHROPIC_API_KEY`
4. Railway will automatically detect the `Procfile` and deploy

### Heroku

```bash
heroku create your-app-name
heroku config:set ANTHROPIC_API_KEY=your_key_here
git push heroku main
```

### Docker (coming soon)

## Configuration ⚙️

### Environment Variables

- `ANTHROPIC_API_KEY` - Your Anthropic API key (required for Claude)
- `KIMI_API_KEY` - Your Kimi API key (optional)
- `PORT` - Port for web server (default: 8000)

### Switching Models

In terminal:
```bash
You: model
Choose (1 or 2):
1. Claude Sonnet 4.5 (Anthropic) - Most capable
2. Kimi K2 (Moonshot) - Cost-effective alternative
```

Via API:
```bash
curl -X POST http://localhost:8000/api/model/switch \
  -H "Content-Type: application/json" \
  -d '{"model_provider": "kimi"}'
```

## Project Structure 📁

```
anthropic-test/
├── main.py                 # Entry point
├── api_server.py          # FastAPI web server
├── terminal_interface.py  # Terminal interface
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── start.sh              # Convenience startup script
├── .env.example          # Environment variables template
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── primary_agent.py       # Primary orchestrator
│   ├── specialized_agents.py  # Specialized agents factory
│   └── tools.py               # Agent tools (search, code exec, etc.)
└── README.md
```

## Available Tools 🛠️

Agents have access to these tools:

1. **web_search** - Search the web for information
2. **fetch_webpage** - Fetch and extract text from URLs
3. **execute_code** - Run Python code safely (sandboxed)
4. **read_file** - Read file contents
5. **write_file** - Write content to files

## Terminal Commands

- `help` - Show available commands
- `agents` - List all specialized agents
- `status` - Show system status and active agents
- `reset` - Clear conversation history
- `model` - Switch between AI models
- `quit` / `exit` - Exit the program

## Troubleshooting 🔧

### "No API keys found"
Make sure you've set `ANTHROPIC_API_KEY` or `KIMI_API_KEY` in your environment or `.env` file.

### "Port already in use"
Change the port:
```bash
PORT=8080 python main.py web
```

### Import errors
Make sure you've installed dependencies:
```bash
pip install -r requirements.txt
```

### Agent not responding
Check your API key is valid and you have credits available.

## Future Enhancements 🔮

- [ ] Persistent conversation storage (database)
- [ ] User authentication and multi-user support
- [ ] Real web search integration (Tavily, Brave Search)
- [ ] Docker containerization
- [ ] More specialized agents (data analysis, creative writing, etc.)
- [ ] Agent collaboration (multiple agents working together)
- [ ] File upload support in web UI
- [ ] Voice input/output
- [ ] Mobile app (React Native)

## Contributing 🤝

Feel free to open issues or submit pull requests!

## License 📄

MIT License - feel free to use this for your own projects!

## Support 💬

If you encounter issues or have questions, please open an issue on GitHub.

---

Built with ❤️ using Claude Sonnet 4.5
