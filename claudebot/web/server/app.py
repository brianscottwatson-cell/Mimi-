import os
import json as _json
from datetime import datetime, timezone

import anthropic
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient

# Import shared Mimi brain — env loading happens on import
from mimi_core import (
    SYSTEM_PROMPT, MODEL, IMAGE_TYPES,
    sync_client as client,
    chat_with_mimi,
    process_image_bytes, process_document_bytes,
    strip_markdown, pcm_to_wav, xai_tts_sync,
    XAI_API_KEY, XAI_VOICE, XAI_TTS_SAMPLE_RATE,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
)

# Google services (optional — graceful if not authed)
try:
    from google_services import (
        gmail_check_inbox, gmail_read_message, gmail_send, gmail_reply,
        calendar_list_events, calendar_create_event, calendar_delete_event,
        docs_create, docs_read, docs_append, drive_list_files,
        google_status,
    )
    GOOGLE_AVAILABLE = google_status().get("authenticated", False)
except Exception:
    GOOGLE_AVAILABLE = False

# GitHub repo tools (for Mimi's GitHub Pages site)
try:
    from github_tools import (
        github_list_files, github_read_file,
        github_create_file, github_update_file,
        github_delete_file, github_get_pages_status,
        GITHUB_AVAILABLE,
    )
except Exception:
    GITHUB_AVAILABLE = False

# Claude Code dispatch (Mimi's self-update capability)
try:
    from claude_dispatch import (
        claude_code_dispatch, claude_code_list_tasks,
        DISPATCH_AVAILABLE,
    )
except Exception:
    DISPATCH_AVAILABLE = False

# Web search (free, no API key)
from web_search import (
    web_search, web_news, web_answers,
    reddit_search, reddit_read_thread,
    x_search, x_news,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "client"))
USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_stats.json")
DASHBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data.json")

app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# Token usage tracking
# ---------------------------------------------------------------------------

# Pricing per million tokens (as of Feb 2026)
MODEL_PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-opus-4-6":            {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5-20251001":  {"input": 0.80, "output": 4.0},
}

def _load_usage():
    try:
        with open(USAGE_FILE, "r") as f:
            return _json.load(f)
    except Exception:
        return {"input_tokens": 0, "output_tokens": 0, "requests": 0, "cost_usd": 0.0}

def _save_usage(usage):
    with open(USAGE_FILE, "w") as f:
        _json.dump(usage, f)

def _track_tokens(response):
    """Extract token usage from a Claude API response and accumulate."""
    usage_data = _load_usage()
    if hasattr(response, "usage"):
        inp = response.usage.input_tokens or 0
        out = response.usage.output_tokens or 0
        usage_data["input_tokens"] += inp
        usage_data["output_tokens"] += out
        usage_data["requests"] += 1
        # Calculate cost
        pricing = MODEL_PRICING.get(MODEL, {"input": 3.0, "output": 15.0})
        cost = (inp / 1_000_000) * pricing["input"] + (out / 1_000_000) * pricing["output"]
        usage_data["cost_usd"] = round(usage_data["cost_usd"] + cost, 6)
        _save_usage(usage_data)
    return usage_data

# ---------------------------------------------------------------------------
# Dashboard data persistence
# ---------------------------------------------------------------------------

_DEFAULT_DASHBOARD = {
    "folders": [
        {"id": "personal", "name": "Personal Life", "icon": "\U0001f3e0"},
        {"id": "work", "name": "Work", "icon": "\U0001f4bc"},
        {"id": "side", "name": "Side Projects", "icon": "\U0001f680"},
    ],
    "projects": [
        {"id": "p1", "folderId": "personal", "name": "Health & Recomp Tracker", "progress": 30, "description": "Track daily macros, workouts, and body recomp progress.", "agents": ["Dev", "Rex"], "prd": "", "rag": "", "created": 1707700000000},
        {"id": "p2", "folderId": "work", "name": "OpenClaw Agent System", "progress": 45, "description": "Build functional multi-agent team with dashboard.", "agents": ["Dev", "Dax", "Pax"], "prd": "", "rag": "", "created": 1707700000001},
        {"id": "p3", "folderId": "work", "name": "Mimi Telegram Integration", "progress": 100, "description": "Deploy Mimi as a Telegram bot on Railway.", "agents": ["Dev"], "prd": "", "rag": "", "created": 1707700000002},
        {"id": "p4", "folderId": "side", "name": "Lead Gen Website Builder", "progress": 10, "description": "Skill for building local service lead gen websites.", "agents": ["Dev", "Dax", "Cora", "Mia", "Rex"], "prd": "", "rag": "", "created": 1707700000003},
    ],
    "tasks": [
        {"text": "Research competitor landscape Q1 2026", "agent": "Rex", "status": "active"},
        {"text": "Draft partner email sequence", "agent": "Cora", "status": "active"},
        {"text": "Design agent dashboard v1", "agent": "Dax", "status": "done"},
        {"text": "Deploy Mimi Telegram bot to Railway", "agent": "Dev", "status": "done"},
        {"text": "Build monthly budget model", "agent": "Finn", "status": "active"},
        {"text": "Create project kickoff template", "agent": "Pax", "status": "done"},
        {"text": "Plan LinkedIn content calendar", "agent": "Mia", "status": "pending"},
        {"text": "Integrate Google services (Gmail/Cal/Docs)", "agent": "Dev", "status": "done"},
        {"text": "Add Reddit & X research tools", "agent": "Dev", "status": "done"},
    ],
    "activity": [
        {"time": "14:15", "text": "Reddit & X research tools added to all agents"},
        {"time": "13:48", "text": "Google services connected (Gmail/Calendar/Docs)"},
        {"time": "13:30", "text": "Lead Gen Website Builder skill installed"},
        {"time": "10:31", "text": "Mimi deployed to Telegram via Railway"},
        {"time": "10:25", "text": "Dev pushed mimi_core.py + telegram_bot.py"},
        {"time": "10:20", "text": "Pax created OpenClaw agent definitions"},
        {"time": "09:58", "text": "Dax designed dashboard layout"},
    ],
}

def _load_dashboard():
    try:
        with open(DASHBOARD_FILE, "r") as f:
            return _json.load(f)
    except Exception:
        data = _json.loads(_json.dumps(_DEFAULT_DASHBOARD))
        _save_dashboard(data)
        return data

def _save_dashboard(data):
    with open(DASHBOARD_FILE, "w") as f:
        _json.dump(data, f, ensure_ascii=False, indent=2)

def _log_activity(text):
    """Append an entry to the dashboard activity feed."""
    data = _load_dashboard()
    now = datetime.now(timezone.utc)
    time_str = now.strftime("%H:%M")
    data["activity"].insert(0, {"time": time_str, "text": text})
    data["activity"] = data["activity"][:50]  # keep last 50
    _save_dashboard(data)

# ---------------------------------------------------------------------------
# In-memory conversation history
# ---------------------------------------------------------------------------

history: list[dict] = []

# ---------------------------------------------------------------------------
# Twilio SMS config
# ---------------------------------------------------------------------------

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
_allowed_sms = os.getenv("TWILIO_ALLOWED_NUMBERS", "").strip()
TWILIO_ALLOWED_NUMBERS = {n.strip() for n in _allowed_sms.split(",") if n.strip()} if _allowed_sms else set()

# Per-phone SMS conversation history (phone -> list of messages)
sms_history: dict[str, list[dict]] = {}
SMS_MAX_HISTORY = 30  # Keep last 30 messages per phone number

# Twilio REST client for outbound SMS
TWILIO_AVAILABLE = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_AVAILABLE else None


def sms_send(phone_number: str, message: str) -> dict:
    """Send an outbound SMS via Twilio."""
    if not twilio_client:
        return {"error": "Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER."}
    try:
        msg = twilio_client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=message[:1600],  # Twilio limit
        )
        _log_activity(f"SMS sent to ...{phone_number[-4:]}: {message[:40]}")
        return {"status": "sent", "sid": msg.sid, "to": phone_number}
    except Exception as e:
        return {"error": f"SMS send failed: {e}"}


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _check_auth():
    token = request.headers.get("X-Netrunner-Token", "").strip()
    if not token:
        return jsonify({"error": "Unauthorized. X-Netrunner-Token header required."}), 401
    return None

# ---------------------------------------------------------------------------
# Build messages for Claude API from conversation history
# ---------------------------------------------------------------------------

def _build_messages():
    """Convert our history into Claude API message format."""
    messages = []
    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        content = entry.get("api_content", entry["content"])
        messages.append({"role": role, "content": content})
    return messages

# ---------------------------------------------------------------------------
# Web Search Tools for Claude
# ---------------------------------------------------------------------------

WEB_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Returns titles, URLs, and snippets. Use for any question about current events, prices, people, companies, or facts you don't know.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {"type": "integer", "description": "Max results to return (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_news",
        "description": "Search for recent news articles. Use for current events, breaking news, industry updates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "News search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_answers",
        "description": "Get instant answers for factual queries like stock prices, weather, definitions, calculations, conversions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or lookup query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "reddit_search",
        "description": "Search Reddit for posts and discussions. Great for product reviews, opinions, recommendations, troubleshooting, and community discussions. Can filter by subreddit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "subreddit": {"type": "string", "description": "Optional: limit to a specific subreddit (e.g. 'fitness', 'technology')"},
                "sort": {"type": "string", "enum": ["relevance", "hot", "top", "new", "comments"], "description": "Sort order (default: relevance)"},
                "max_results": {"type": "integer", "description": "Max results (default 8)", "default": 8},
            },
            "required": ["query"],
        },
    },
    {
        "name": "reddit_read_thread",
        "description": "Read a specific Reddit thread including top comments. Pass a full Reddit URL from a previous search result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full Reddit thread URL"},
                "max_comments": {"type": "integer", "description": "Max comments to read (default 10)", "default": 10},
            },
            "required": ["url"],
        },
    },
    {
        "name": "x_search",
        "description": "Search X (Twitter) for posts, takes, and discussions. Good for trending topics, real-time reactions, public figures' statements, and industry chatter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 8)", "default": 8},
            },
            "required": ["query"],
        },
    },
    {
        "name": "x_news",
        "description": "Search for news coverage of X/Twitter discussions and viral posts on a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic to find X-related news about"},
                "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
]

WEB_HANDLERS = {
    "web_search": lambda **kw: web_search(**kw),
    "web_news": lambda **kw: web_news(**kw),
    "web_answers": lambda **kw: web_answers(**kw),
    "reddit_search": lambda **kw: reddit_search(**kw),
    "reddit_read_thread": lambda **kw: reddit_read_thread(**kw),
    "x_search": lambda **kw: x_search(**kw),
    "x_news": lambda **kw: x_news(**kw),
}

# ---------------------------------------------------------------------------
# Google Service Tools for Claude
# ---------------------------------------------------------------------------

GOOGLE_TOOLS = [
    {
        "name": "gmail_check_inbox",
        "description": "Check Gmail inbox for recent messages. Returns subject, sender, date, and snippet for each.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Max emails to return (default 5)", "default": 5},
                "query": {"type": "string", "description": "Gmail search query (default 'is:unread')", "default": "is:unread"},
            },
        },
    },
    {
        "name": "gmail_read_message",
        "description": "Read the full content of a specific email by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string", "description": "The Gmail message ID"}},
            "required": ["message_id"],
        },
    },
    {
        "name": "gmail_send",
        "description": "Send a new email from msmimibot2@gmail.com.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body text"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "gmail_reply",
        "description": "Reply to an existing email thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "ID of the message to reply to"},
                "body": {"type": "string", "description": "Reply body text"},
            },
            "required": ["message_id", "body"],
        },
    },
    {
        "name": "calendar_list_events",
        "description": "List upcoming Google Calendar events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Number of days to look ahead (default 7)", "default": 7},
                "max_results": {"type": "integer", "description": "Max events to return (default 10)", "default": 10},
            },
        },
    },
    {
        "name": "calendar_create_event",
        "description": "Create a new Google Calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time in ISO format (e.g. 2026-02-15T10:00:00-07:00)"},
                "end_time": {"type": "string", "description": "End time in ISO format"},
                "description": {"type": "string", "description": "Event description (optional)"},
                "location": {"type": "string", "description": "Event location (optional)"},
            },
            "required": ["summary", "start_time", "end_time"],
        },
    },
    {
        "name": "calendar_delete_event",
        "description": "Delete a Google Calendar event by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The calendar event ID"}},
            "required": ["event_id"],
        },
    },
    {
        "name": "docs_create",
        "description": "Create a new Google Doc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "body_text": {"type": "string", "description": "Initial text content (optional)"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "docs_read",
        "description": "Read the text content of an existing Google Doc by its document ID.",
        "input_schema": {
            "type": "object",
            "properties": {"document_id": {"type": "string", "description": "The Google Doc ID"}},
            "required": ["document_id"],
        },
    },
    {
        "name": "docs_append",
        "description": "Append text to the end of an existing Google Doc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "The Google Doc ID"},
                "text": {"type": "string", "description": "Text to append"},
            },
            "required": ["document_id", "text"],
        },
    },
    {
        "name": "drive_list_files",
        "description": "List files in Google Drive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Drive search query (optional)"},
                "max_results": {"type": "integer", "description": "Max files to return (default 10)", "default": 10},
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Dashboard Tools for Claude (so Mimi can manage the dashboard)
# ---------------------------------------------------------------------------

DASHBOARD_TOOLS = [
    {
        "name": "dashboard_create_project",
        "description": "Create a new project on the OpenClaw dashboard. Use when Brian asks to start a new project or initiative.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "folder": {"type": "string", "description": "Folder ID: 'personal', 'work', or 'side'", "default": "side"},
                "description": {"type": "string", "description": "Project description"},
                "agents": {"type": "array", "items": {"type": "string"}, "description": "Agent names to assign (e.g. ['Dev', 'Rex'])"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "dashboard_update_project",
        "description": "Update an existing project on the dashboard (progress, agents, PRD, status).",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Project ID (e.g. 'p1')"},
                "progress": {"type": "integer", "description": "Progress percentage (0-100)"},
                "agents": {"type": "array", "items": {"type": "string"}, "description": "Updated agent list"},
                "prd": {"type": "string", "description": "PRD summary text"},
                "status": {"type": "string", "description": "Project status note"},
                "description": {"type": "string", "description": "Updated description"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "dashboard_create_task",
        "description": "Create a new task on the dashboard. Use when Brian or an agent needs a new task tracked.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Task description"},
                "agent": {"type": "string", "description": "Agent to assign (Rex, Cora, Dax, Dev, Finn, Pax, Mia, Vale)"},
                "status": {"type": "string", "enum": ["pending", "active", "done"], "description": "Task status (default: pending)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "dashboard_update_task",
        "description": "Update a task's status on the dashboard. Use when a task is started, completed, or reassigned.",
        "input_schema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "Task index (0-based)"},
                "status": {"type": "string", "enum": ["pending", "active", "done"], "description": "New status"},
            },
            "required": ["index", "status"],
        },
    },
    {
        "name": "dashboard_log_activity",
        "description": "Log an activity entry to the dashboard feed. Use for notable events, milestones, or completions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Activity description"},
            },
            "required": ["text"],
        },
    },
]


GITHUB_TOOLS = [
    {
        "name": "github_list_files",
        "description": "List files and directories in the Mimi GitHub Pages repo. Use to browse the site structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list (default: repo root)", "default": ""},
                "recursive": {"type": "boolean", "description": "Include one level of subdirectories", "default": False},
            },
        },
    },
    {
        "name": "github_read_file",
        "description": "Read a file from the Mimi GitHub Pages repo. Returns content and SHA (needed for updates).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root (e.g. 'agents/openclaw/dashboard.html')"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "github_create_file",
        "description": "Create a NEW file in the Mimi GitHub Pages repo. Goes live in ~30 seconds. Fails if file exists.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to create (e.g. 'projects.html')"},
                "content": {"type": "string", "description": "Full file content (HTML, CSS, JS, Markdown, etc.)"},
                "commit_message": {"type": "string", "description": "Git commit message (auto-generated if omitted)"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "github_update_file",
        "description": "Update an EXISTING file in the Mimi GitHub Pages repo. Auto-fetches SHA. Goes live in ~30 seconds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to update"},
                "content": {"type": "string", "description": "Complete new file content (replaces entire file)"},
                "commit_message": {"type": "string", "description": "Git commit message (auto-generated if omitted)"},
                "sha": {"type": "string", "description": "File SHA from github_read_file (auto-fetched if omitted)"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "github_delete_file",
        "description": "Delete a file from the Mimi GitHub Pages repo. Cannot delete protected server files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to delete"},
                "commit_message": {"type": "string", "description": "Git commit message (auto-generated if omitted)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "github_get_pages_status",
        "description": "Check GitHub Pages deployment status and view recent commits.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


def _handle_dashboard_tool(tool_name, tool_input):
    """Execute a dashboard tool and return the result."""
    data = _load_dashboard()

    if tool_name == "dashboard_create_project":
        project = {
            "id": "p" + str(int(datetime.now(timezone.utc).timestamp() * 1000)),
            "folderId": tool_input.get("folder", "side"),
            "name": tool_input["name"],
            "progress": 0,
            "description": tool_input.get("description", ""),
            "agents": tool_input.get("agents", []),
            "prd": "",
            "rag": "",
            "created": int(datetime.now(timezone.utc).timestamp() * 1000),
        }
        data["projects"].append(project)
        _save_dashboard(data)
        _log_activity(f'New project created: "{project["name"]}"')
        return {"status": "created", "project": project}

    elif tool_name == "dashboard_update_project":
        project = next((p for p in data["projects"] if p["id"] == tool_input["id"]), None)
        if not project:
            return {"error": f"Project {tool_input['id']} not found"}
        for key in ("progress", "agents", "prd", "status", "description"):
            if key in tool_input:
                project[key] = tool_input[key]
        _save_dashboard(data)
        _log_activity(f'Project "{project["name"]}" updated')
        return {"status": "updated", "project": project}

    elif tool_name == "dashboard_create_task":
        task = {
            "text": tool_input["text"],
            "agent": tool_input.get("agent", ""),
            "status": tool_input.get("status", "pending"),
        }
        data["tasks"].insert(0, task)
        _save_dashboard(data)
        _log_activity(f'New task: "{task["text"]}"')
        return {"status": "created", "task": task}

    elif tool_name == "dashboard_update_task":
        idx = int(tool_input["index"])
        if idx < 0 or idx >= len(data["tasks"]):
            return {"error": f"Task index {idx} out of range (0-{len(data['tasks'])-1})"}
        task = data["tasks"][idx]
        old_status = task["status"]
        task["status"] = tool_input["status"]
        _save_dashboard(data)
        if tool_input["status"] == "done" and old_status != "done":
            _log_activity(f'{task["agent"]} completed: "{task["text"]}"')
        return {"status": "updated", "task": task}

    elif tool_name == "dashboard_log_activity":
        _log_activity(tool_input["text"])
        return {"status": "logged"}

    return {"error": f"Unknown dashboard tool: {tool_name}"}


# Map tool names to functions
TOOL_HANDLERS = dict(WEB_HANDLERS)  # Web search always available
if GOOGLE_AVAILABLE:
    TOOL_HANDLERS.update({
        "gmail_check_inbox": lambda **kw: gmail_check_inbox(**kw),
        "gmail_read_message": lambda **kw: gmail_read_message(**kw),
        "gmail_send": lambda **kw: gmail_send(**kw),
        "gmail_reply": lambda **kw: gmail_reply(**kw),
        "calendar_list_events": lambda **kw: calendar_list_events(**kw),
        "calendar_create_event": lambda **kw: calendar_create_event(**kw),
        "calendar_delete_event": lambda **kw: calendar_delete_event(**kw),
        "docs_create": lambda **kw: docs_create(**kw),
        "docs_read": lambda **kw: docs_read(**kw),
        "docs_append": lambda **kw: docs_append(**kw),
        "drive_list_files": lambda **kw: drive_list_files(**kw),
    })

# Dashboard tools (use a dispatcher since they share _handle_dashboard_tool)
for _dt in DASHBOARD_TOOLS:
    _tool_name = _dt["name"]
    TOOL_HANDLERS[_tool_name] = (lambda tn: lambda **kw: _handle_dashboard_tool(tn, kw))(_tool_name)

# GitHub tools (if GITHUB_TOKEN is set)
if GITHUB_AVAILABLE:
    TOOL_HANDLERS.update({
        "github_list_files": lambda **kw: github_list_files(**kw),
        "github_read_file": lambda **kw: github_read_file(**kw),
        "github_create_file": lambda **kw: github_create_file(**kw),
        "github_update_file": lambda **kw: github_update_file(**kw),
        "github_delete_file": lambda **kw: github_delete_file(**kw),
        "github_get_pages_status": lambda **kw: github_get_pages_status(**kw),
    })

# ---------------------------------------------------------------------------
# SMS Outbound Tool for Claude
# ---------------------------------------------------------------------------

SMS_TOOLS = [
    {
        "name": "sms_send",
        "description": "Send an SMS text message to a phone number via Twilio. Use this when Brian asks you to text someone, send an SMS, or when you need to proactively notify Brian about something important. Phone numbers must be in E.164 format (e.g. +13035551234).",
        "input_schema": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "description": "Recipient phone number in E.164 format (e.g. +13035551234)"},
                "message": {"type": "string", "description": "The message text to send (max 1600 chars)"},
            },
            "required": ["phone_number", "message"],
        },
    },
]

if TWILIO_AVAILABLE:
    TOOL_HANDLERS["sms_send"] = lambda **kw: sms_send(**kw)

# ---------------------------------------------------------------------------
# Claude Code Dispatch Tools (Mimi's self-update capability)
# ---------------------------------------------------------------------------

DISPATCH_TOOLS = [
    {
        "name": "claude_code_dispatch",
        "description": "Dispatch a development task to Claude Code. Use this when Brian asks for code changes, new features, bug fixes, new agents, or any modification to the Mimi codebase. Creates a GitHub Issue that Claude Code will pick up and implement, then creates a PR. Examples: 'Add a new agent', 'Fix the SMS sending', 'Update the dashboard UI'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Clear description of what needs to be built, fixed, or changed"},
                "files_to_modify": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of file paths that likely need changes",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority (default: medium)",
                },
                "branch_name": {"type": "string", "description": "Optional git branch name for this work"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "claude_code_list_tasks",
        "description": "List existing development tasks dispatched to Claude Code. Shows open/closed issues labeled 'claude-code'. Use to check on pending work or review completed tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Filter by issue state (default: open)",
                },
            },
        },
    },
]

if DISPATCH_AVAILABLE:
    TOOL_HANDLERS["claude_code_dispatch"] = lambda **kw: claude_code_dispatch(**kw)
    TOOL_HANDLERS["claude_code_list_tasks"] = lambda **kw: claude_code_list_tasks(**kw)


def _chat_with_tools(messages):
    """Chat with Mimi using tool use for web search + Google services + dashboard + GitHub + SMS + dispatch."""
    tools = list(WEB_TOOLS)  # Web search always available
    if GOOGLE_AVAILABLE:
        tools.extend(GOOGLE_TOOLS)
    tools.extend(DASHBOARD_TOOLS)
    if GITHUB_AVAILABLE:
        tools.extend(GITHUB_TOOLS)
    if TWILIO_AVAILABLE:
        tools.extend(SMS_TOOLS)
    if DISPATCH_AVAILABLE:
        tools.extend(DISPATCH_TOOLS)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=tools if tools else anthropic.NOT_GIVEN,
    )
    _track_tokens(response)

    # Handle tool use loop (max 5 rounds to prevent infinite loops)
    for _ in range(5):
        if response.stop_reason != "tool_use":
            break

        # Extract text and tool calls from response
        assistant_content = response.content
        tool_results = []

        for block in assistant_content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    try:
                        result = handler(**tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": _json.dumps(result, default=str, ensure_ascii=False),
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool '{tool_name}' not available.",
                        "is_error": True,
                    })

        # Continue conversation with tool results
        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )
        _track_tokens(response)

    # Extract final text response
    text_parts = [b.text for b in response.content if hasattr(b, "text")]
    return "\n".join(text_parts) if text_parts else "Done."

def _process_uploaded_files(files):
    """Process uploaded files into Claude API content blocks."""
    content_blocks = []
    file_descriptions = []

    for f in files:
        mime = f.content_type or ""
        name = f.filename or "file"
        data = f.read()

        if mime in IMAGE_TYPES:
            content_blocks.append(process_image_bytes(data, mime, name))
            file_descriptions.append(f"[Image: {name}]")
        else:
            block = process_document_bytes(data, name)
            if block:
                content_blocks.append(block)
                file_descriptions.append(f"[Document: {name}]")
            else:
                file_descriptions.append(f"[Unsupported file: {name}]")

    return content_blocks, file_descriptions

# ---------------------------------------------------------------------------
# Routes — static
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(CLIENT_DIR, "index.html")

# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    # Handle both JSON and multipart form data
    file_content_blocks = []
    file_descriptions = []

    if request.content_type and "multipart" in request.content_type:
        user_message = request.form.get("message", "").strip()
        uploaded_files = request.files.getlist("files")
        if uploaded_files:
            file_content_blocks, file_descriptions = _process_uploaded_files(uploaded_files)
    else:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()

    if not user_message and not file_content_blocks:
        return jsonify({"error": "Missing 'message' field."}), 400

    now = datetime.now(timezone.utc).isoformat()

    # Build display text for history
    display_text = user_message
    if file_descriptions:
        display_text = (user_message + " " + " ".join(file_descriptions)).strip()

    # Build API content (may include image blocks)
    api_content = []
    if file_content_blocks:
        api_content.extend(file_content_blocks)
    if user_message:
        api_content.append({"type": "text", "text": user_message})
    elif file_content_blocks:
        api_content.append({"type": "text", "text": "Please analyze the attached file(s)."})

    # Store user message (display_text for UI, api_content for Claude)
    history.append({
        "role": "user",
        "content": display_text,
        "api_content": api_content,
        "timestamp": now,
    })

    # Call Claude API with tools (web search always available, Google if authed)
    try:
        messages = _build_messages()
        reply = _chat_with_tools(messages)
    except Exception as e:
        reply = f"[LINK ERROR] Something went sideways: {e}"

    now = datetime.now(timezone.utc).isoformat()
    history.append({"role": "bot", "content": reply, "timestamp": now})

    # Auto-log chat activity to dashboard
    try:
        snippet = user_message[:60] if user_message else "file upload"
        _log_activity(f"Chat: {snippet}")
    except Exception:
        pass

    return jsonify({"reply": reply, "timestamp": now})


@app.route("/api/history", methods=["GET"])
def get_history():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    return jsonify(history)


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    history.clear()
    return jsonify({"status": "History cleared."})

# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

@app.route("/api/tts", methods=["POST"])
def tts():
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing 'text' field."}), 400

    clean_text = strip_markdown(text)
    if not clean_text:
        return jsonify({"error": "No speakable text."}), 400

    if len(clean_text) > 1500:
        clean_text = clean_text[:1500] + "... and that's the summary."

    # ── Priority 1: x.ai Eve voice (WebSocket Realtime API) ────────────
    if XAI_API_KEY:
        try:
            wav_data = xai_tts_sync(clean_text, XAI_VOICE)
            return Response(
                wav_data,
                mimetype="audio/wav",
                headers={"Content-Disposition": "inline"},
            )
        except Exception as exc:
            app.logger.warning("x.ai TTS failed, falling through: %s", exc)

    # ── Priority 2: ElevenLabs ─────────────────────────────────────────
    if ELEVENLABS_API_KEY:
        try:
            import requests as http_requests
            resp = http_requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": clean_text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.3,
                        "use_speaker_boost": True,
                    },
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return Response(
                    resp.content,
                    mimetype="audio/mpeg",
                    headers={"Content-Disposition": "inline"},
                )
        except Exception:
            pass

    # ── Priority 3: Browser speechSynthesis fallback ───────────────────
    return jsonify({"fallback": True, "text": clean_text})


@app.route("/api/tts/status", methods=["GET"])
def tts_status():
    """Report which TTS providers are configured."""
    return jsonify({
        "xai": bool(XAI_API_KEY),
        "xai_voice": XAI_VOICE if XAI_API_KEY else None,
        "elevenlabs": bool(ELEVENLABS_API_KEY),
        "elevenlabs_voice_id": ELEVENLABS_VOICE_ID if ELEVENLABS_API_KEY else None,
    })


# ---------------------------------------------------------------------------
# SMS (Twilio webhook)
# ---------------------------------------------------------------------------

def _sms_chat(phone: str, user_text: str) -> str:
    """Process an SMS message through Mimi with full tool access."""
    if phone not in sms_history:
        sms_history[phone] = []

    sms_history[phone].append({"role": "user", "content": user_text})

    # Trim to keep history manageable
    if len(sms_history[phone]) > SMS_MAX_HISTORY:
        sms_history[phone] = sms_history[phone][-SMS_MAX_HISTORY:]

    try:
        reply = _chat_with_tools(list(sms_history[phone]))
    except Exception as e:
        reply = f"Something went sideways: {e}"

    sms_history[phone].append({"role": "assistant", "content": reply})
    return reply


@app.route("/sms/webhook", methods=["POST"])
def sms_webhook():
    """Twilio webhook — receives incoming SMS and replies as Mimi."""
    from_number = request.form.get("From", "")
    body = request.form.get("Body", "").strip()

    # Optional: restrict to allowed numbers
    if TWILIO_ALLOWED_NUMBERS and from_number not in TWILIO_ALLOWED_NUMBERS:
        resp = MessagingResponse()
        resp.message("This number is not authorized to talk to Mimi.")
        return str(resp), 200, {"Content-Type": "application/xml"}

    if not body:
        resp = MessagingResponse()
        resp.message("Send me a message and I'll respond!")
        return str(resp), 200, {"Content-Type": "application/xml"}

    # Handle /clear command
    if body.lower() in ("/clear", "clear history", "reset"):
        sms_history.pop(from_number, None)
        resp = MessagingResponse()
        resp.message("History cleared. Fresh start!")
        return str(resp), 200, {"Content-Type": "application/xml"}

    # Process through Mimi
    reply = _sms_chat(from_number, body)

    # Auto-log SMS activity to dashboard
    try:
        phone_short = from_number[-4:] if len(from_number) >= 4 else from_number
        snippet = body[:40]
        _log_activity(f"SMS from ...{phone_short}: {snippet}")
    except Exception:
        pass

    # Twilio handles splitting long messages automatically (1600 char segments)
    # but we'll cap at a reasonable length for readability
    if len(reply) > 1500:
        reply = reply[:1497] + "..."

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp), 200, {"Content-Type": "application/xml"}


# ---------------------------------------------------------------------------
# Capabilities status
# ---------------------------------------------------------------------------

@app.route("/api/capabilities", methods=["GET"])
def capabilities():
    """Report all connected tools and services."""
    return jsonify({
        "google": GOOGLE_AVAILABLE,
        "github": GITHUB_AVAILABLE,
        "sms_outbound": TWILIO_AVAILABLE,
        "sms_inbound": bool(TWILIO_ACCOUNT_SID),
        "claude_dispatch": DISPATCH_AVAILABLE,
        "tts_xai": bool(XAI_API_KEY),
        "tts_elevenlabs": bool(ELEVENLABS_API_KEY),
        "web_search": True,
    })


# ---------------------------------------------------------------------------
# Usage stats
# ---------------------------------------------------------------------------

@app.route("/api/usage", methods=["GET"])
def usage_stats():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    usage = _load_usage()
    usage["model"] = MODEL
    return jsonify(usage)


@app.route("/api/usage/reset", methods=["POST"])
def usage_reset():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    _save_usage({"input_tokens": 0, "output_tokens": 0, "requests": 0, "cost_usd": 0.0})
    return jsonify({"status": "Usage stats reset."})


# ---------------------------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def dashboard_get():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    return jsonify(_load_dashboard())


@app.route("/api/dashboard/projects", methods=["POST"])
def dashboard_create_project():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    body = request.get_json(silent=True) or {}
    name = body.get("name", "").strip()
    if not name:
        return jsonify({"error": "Missing 'name'"}), 400
    data = _load_dashboard()
    project = {
        "id": "p" + str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "folderId": body.get("folderId", body.get("folder", "side")),
        "name": name,
        "progress": int(body.get("progress", 0)),
        "description": body.get("description", ""),
        "agents": body.get("agents", []),
        "prd": body.get("prd", ""),
        "rag": body.get("rag", ""),
        "created": int(datetime.now(timezone.utc).timestamp() * 1000),
    }
    data["projects"].append(project)
    _save_dashboard(data)
    _log_activity(f'New project created: "{name}"')
    return jsonify(project), 201


@app.route("/api/dashboard/projects", methods=["PUT"])
def dashboard_update_project():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    body = request.get_json(silent=True) or {}
    project_id = body.get("id", "")
    if not project_id:
        return jsonify({"error": "Missing 'id'"}), 400
    data = _load_dashboard()
    project = next((p for p in data["projects"] if p["id"] == project_id), None)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    for key in ("name", "folderId", "description", "prd", "rag", "status"):
        if key in body:
            project[key] = body[key]
    if "progress" in body:
        project["progress"] = int(body["progress"])
    if "agents" in body:
        project["agents"] = body["agents"]
    _save_dashboard(data)
    return jsonify(project)


@app.route("/api/dashboard/tasks", methods=["POST"])
def dashboard_create_task():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    data = _load_dashboard()
    task = {
        "text": text,
        "agent": body.get("agent", ""),
        "status": body.get("status", "pending"),
    }
    data["tasks"].insert(0, task)
    _save_dashboard(data)
    if task["agent"]:
        _log_activity(f'New task assigned to {task["agent"]}: "{text}"')
    else:
        _log_activity(f'New task: "{text}"')
    return jsonify(task), 201


@app.route("/api/dashboard/tasks", methods=["PUT"])
def dashboard_update_task():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    body = request.get_json(silent=True) or {}
    index = body.get("index")
    if index is None:
        return jsonify({"error": "Missing 'index'"}), 400
    data = _load_dashboard()
    index = int(index)
    if index < 0 or index >= len(data["tasks"]):
        return jsonify({"error": "Task index out of range"}), 404
    task = data["tasks"][index]
    if "status" in body:
        old_status = task["status"]
        task["status"] = body["status"]
        if body["status"] == "done" and old_status != "done":
            _log_activity(f'{task["agent"]} completed: "{task["text"]}"')
    if "text" in body:
        task["text"] = body["text"]
    if "agent" in body:
        task["agent"] = body["agent"]
    _save_dashboard(data)
    return jsonify(task)


@app.route("/api/dashboard/activity", methods=["POST"])
def dashboard_log_activity():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    _log_activity(text)
    return jsonify({"status": "ok"}), 201


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Mimi Gateway v1.0 — Model: {MODEL}")
    print(f"Serving frontend from: {CLIENT_DIR}")
    app.run(host="0.0.0.0", port=port, debug=True)
