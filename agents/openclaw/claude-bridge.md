# Mimi ↔ Claude Code Bridge

## Purpose
Allows Mimi to autonomously trigger development work through Claude Code API,
so Brian can just talk to Mimi and she handles the implementation by dispatching
to Claude.

## How It Works

```
Brian → Mimi (chat/SMS/Telegram)
  "Add a new skill to Rex" or "Fix the SMS sending"
    ↓
Mimi analyzes the request
    ↓
Mimi calls `claude_code_dispatch` tool
    ↓
Claude Code API creates a task on the repo
    ↓
Changes committed to branch → PR created
    ↓
Mimi reports back to Brian with a link
```

## Integration Points

### 1. Claude Code Task API
Mimi can create tasks via the Claude Code API that:
- Open a session on the `brianscottwatson-cell/Mimi-` repo
- Execute the requested changes (add files, edit code, etc.)
- Commit to a feature branch
- Create a PR for review

### 2. GitHub Actions (Alternative)
If direct API isn't available, Mimi can:
- Create a GitHub Issue with the task description
- A GitHub Action triggers Claude Code to work on it
- Results pushed as a PR

### 3. Webhook Dispatch
Mimi's Flask server can expose a `/dev/dispatch` endpoint that:
- Receives structured task descriptions
- Queues them for Claude Code processing
- Returns task status and PR links

## Tool Definition (for Mimi's tool-use system)

```python
{
    "name": "claude_code_dispatch",
    "description": "Dispatch a development task to Claude Code. Use this when Brian asks for code changes, new features, bug fixes, new agents, or any modification to the Mimi- repository. Claude will make the changes and create a PR.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Clear description of what needs to be built, fixed, or changed"
            },
            "files_to_modify": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths that likely need changes (optional)"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Task priority level"
            },
            "branch_name": {
                "type": "string",
                "description": "Git branch name for this work (optional, auto-generated if not provided)"
            }
        },
        "required": ["task"]
    }
}
```

## Setup Required
1. Claude Code API access or GitHub App installation
2. Repository write access for `brianscottwatson-cell/Mimi-`
3. Webhook URL configured in Mimi's environment
4. GitHub token with PR creation permissions (already have `GITHUB_TOKEN`)

## Environment Variables
```
CLAUDE_CODE_API_KEY=...          # If using direct API
CLAUDE_CODE_WEBHOOK_URL=...      # If using webhook dispatch
GITHUB_TOKEN=...                 # Already configured for GitHub Pages
```
