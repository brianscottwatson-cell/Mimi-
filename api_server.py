"""
FastAPI web server for the multi-agent system.
Provides REST API endpoints and serves the web UI.
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import PrimaryAgent
import uvicorn

# Load environment variables from .env file
load_dotenv()


# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    agent_used: str
    delegated: bool
    session_id: str
    timestamp: str


class ModelSwitchRequest(BaseModel):
    model_provider: str  # "anthropic" or "kimi"
    model_name: Optional[str] = None


class StatusResponse(BaseModel):
    status: str
    model_provider: str
    model_name: str
    active_sessions: int
    available_agents: list


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent AI System",
    description="Primary agent with specialized sub-agents for various domains",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets directory
assets_path = os.path.join(os.path.dirname(__file__), "web", "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# Global state
sessions: Dict[str, PrimaryAgent] = {}
current_model_provider = "anthropic"
current_model_name = "claude-sonnet-4-5-20250929"


def get_or_create_session(session_id: str) -> PrimaryAgent:
    """Get or create a session with a primary agent."""
    if session_id not in sessions:
        sessions[session_id] = PrimaryAgent(
            model_provider=current_model_provider,
            model_name=current_model_name
        )
    return sessions[session_id]


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the web UI."""
    html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")

    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    else:
        # Return a basic embedded UI if the file doesn't exist yet
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent AI System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { font-size: 14px; opacity: 0.9; }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .message.assistant {
            background: white;
            color: #333;
            border: 1px solid #ddd;
        }
        .message.system {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
            text-align: center;
            margin: 10px auto;
            font-size: 13px;
        }
        .agent-badge {
            display: inline-block;
            background: #764ba2;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            margin-bottom: 5px;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
            transition: border 0.3s;
        }
        input[type="text"]:focus {
            border-color: #667eea;
        }
        button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 15px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.05);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .loading {
            text-align: center;
            padding: 10px;
            color: #666;
        }
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Multi-Agent AI System</h1>
            <p>Primary agent with specialized sub-agents</p>
        </div>
        <div class="messages" id="messages">
            <div class="message system">
                Welcome! I'm your primary AI agent. I can help you directly or delegate to specialized agents in research, marketing, SEO, digital marketing, project management, and web development.
            </div>
        </div>
        <div class="input-area">
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Type your message..." />
                <button id="sendButton">Send</button>
            </div>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        function addMessage(content, type, agentUsed = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;

            if (agentUsed && type === 'assistant') {
                const badge = document.createElement('div');
                badge.className = 'agent-badge';
                badge.textContent = agentUsed;
                messageDiv.appendChild(badge);
            }

            const textNode = document.createTextNode(content);
            messageDiv.appendChild(textNode);

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showLoading() {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.id = 'loading';
            loadingDiv.textContent = 'Thinking';
            messagesDiv.appendChild(loadingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function hideLoading() {
            const loadingDiv = document.getElementById('loading');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Disable input
            messageInput.disabled = true;
            sendButton.disabled = true;

            // Add user message
            addMessage(message, 'user');
            messageInput.value = '';

            // Show loading
            showLoading();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message })
                });

                const data = await response.json();

                // Hide loading
                hideLoading();

                if (response.ok) {
                    addMessage(data.response, 'assistant', data.agent_used);
                } else {
                    addMessage(`Error: ${data.detail || 'Unknown error'}`, 'system');
                }
            } catch (error) {
                hideLoading();
                addMessage(`Error: ${error.message}`, 'system');
            } finally {
                // Re-enable input
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
        """


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the primary agent.

    Args:
        request: ChatRequest with message and optional session_id

    Returns:
        ChatResponse with agent's response
    """
    try:
        # Get or create session
        primary_agent = get_or_create_session(request.session_id)

        # Process message
        result = primary_agent.chat(request.message)

        return ChatResponse(
            response=result["response"],
            agent_used=result["agent_used"],
            delegated=result["delegated"],
            session_id=request.session_id,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session(session_id: str = "default"):
    """Reset a session's conversation history."""
    if session_id in sessions:
        sessions[session_id].reset()
        return {"status": "success", "message": f"Session {session_id} reset"}
    else:
        return {"status": "success", "message": "Session not found (nothing to reset)"}


@app.post("/api/model/switch")
async def switch_model(request: ModelSwitchRequest):
    """
    Switch the model provider and/or model name.

    Args:
        request: ModelSwitchRequest with provider and optional model_name

    Returns:
        Status message
    """
    global current_model_provider, current_model_name

    # Validate provider
    if request.model_provider not in ["anthropic", "kimi"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid model provider. Must be 'anthropic' or 'kimi'"
        )

    # Set model name based on provider
    if request.model_name:
        current_model_name = request.model_name
    else:
        # Default models
        if request.model_provider == "anthropic":
            current_model_name = "claude-sonnet-4-5-20250929"
        elif request.model_provider == "kimi":
            current_model_name = "moonshot-v1-8k"

    current_model_provider = request.model_provider

    # Update all existing sessions
    for session in sessions.values():
        session.switch_model(current_model_provider, current_model_name)

    return {
        "status": "success",
        "model_provider": current_model_provider,
        "model_name": current_model_name,
        "message": f"Switched to {current_model_provider} ({current_model_name})"
    }


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status and information."""
    from agents.specialized_agents import SpecializedAgentFactory

    return StatusResponse(
        status="running",
        model_provider=current_model_provider,
        model_name=current_model_name,
        active_sessions=len(sessions),
        available_agents=list(SpecializedAgentFactory.get_all_agent_types().keys())
    )


@app.get("/api/agents")
async def list_agents():
    """List all available specialized agents."""
    from agents.specialized_agents import SpecializedAgentFactory

    return {
        "agents": SpecializedAgentFactory.get_all_agent_types()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server."""
    print(f"🚀 Starting Multi-Agent AI System on http://{host}:{port}")
    print(f"📱 Access from your phone by visiting: http://[your-computer-ip]:{port}")
    print(f"🤖 Current model: {current_model_provider} ({current_model_name})")
    print("\nAPI Endpoints:")
    print(f"  - Web UI: http://{host}:{port}/")
    print(f"  - Chat: POST http://{host}:{port}/api/chat")
    print(f"  - Status: GET http://{host}:{port}/api/status")
    print(f"  - Available Agents: GET http://{host}:{port}/api/agents")
    print(f"  - Switch Model: POST http://{host}:{port}/api/model/switch")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Get port from environment (for Railway/Heroku) or use default
    port = int(os.getenv("PORT", 8000))
    start_server(port=port)
