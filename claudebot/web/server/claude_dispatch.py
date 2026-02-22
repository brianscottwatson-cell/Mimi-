"""Claude Code Dispatch — Mimi's self-update capability.

Allows Mimi to create GitHub Issues (labeled 'claude-code') that trigger
Claude Code to make changes to the Mimi- repository. This is how Mimi
requests development work on herself and her agent team.

Flow:
  1. Brian tells Mimi to add/fix/change something
  2. Mimi creates a GitHub Issue with structured task description
  3. Claude Code picks up the issue (via GitHub Actions or manual trigger)
  4. Changes are committed to a feature branch, PR is created
  5. Mimi reports back with the PR link
"""

import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_OWNER = "brianscottwatson-cell"
GITHUB_REPO = "Mimi-"
GITHUB_API = "https://api.github.com"

DISPATCH_AVAILABLE = bool(GITHUB_TOKEN)


def _headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def claude_code_dispatch(task: str, files_to_modify: list = None,
                         priority: str = "medium", branch_name: str = None) -> dict:
    """Create a GitHub Issue to dispatch a development task to Claude Code.

    Args:
        task: Clear description of what needs to be built, fixed, or changed
        files_to_modify: Optional list of file paths likely to need changes
        priority: low, medium, or high
        branch_name: Optional git branch name for this work
    """
    if not DISPATCH_AVAILABLE:
        return {"error": "GitHub token not configured. Set GITHUB_TOKEN env var."}

    # Build the issue body with structured task info
    body_parts = [
        "## Task Description",
        task,
        "",
        f"**Priority:** {priority}",
        f"**Requested by:** Mimi (automated dispatch)",
    ]

    if files_to_modify:
        body_parts.extend([
            "",
            "## Files to Modify",
            *[f"- `{f}`" for f in files_to_modify],
        ])

    if branch_name:
        body_parts.extend(["", f"**Suggested branch:** `{branch_name}`"])

    body_parts.extend([
        "",
        "---",
        "*This issue was created by Mimi's Claude Code dispatch system.*",
        "*Claude Code should pick this up and create a PR with the changes.*",
    ])

    body = "\n".join(body_parts)

    # Determine labels
    labels = ["claude-code"]
    if priority == "high":
        labels.append("priority:high")
    elif priority == "low":
        labels.append("priority:low")

    # Create the GitHub Issue
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
    payload = {
        "title": f"[Claude Code] {task[:80]}",
        "body": body,
        "labels": labels,
    }

    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
        resp.raise_for_status()
        issue = resp.json()

        return {
            "status": "dispatched",
            "issue_number": issue["number"],
            "issue_url": issue["html_url"],
            "title": issue["title"],
            "message": f"Task dispatched as issue #{issue['number']}. Claude Code will pick this up and create a PR.",
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"Failed to create issue: {e.response.status_code} — {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"Dispatch failed: {e}"}


def claude_code_list_tasks(state: str = "open") -> dict:
    """List existing Claude Code dispatch tasks (issues labeled 'claude-code').

    Args:
        state: 'open', 'closed', or 'all'
    """
    if not DISPATCH_AVAILABLE:
        return {"error": "GitHub token not configured."}

    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
    params = {
        "labels": "claude-code",
        "state": state,
        "per_page": 10,
        "sort": "created",
        "direction": "desc",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=15)
        resp.raise_for_status()
        issues = resp.json()

        tasks = []
        for issue in issues:
            tasks.append({
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "created": issue["created_at"],
                "url": issue["html_url"],
                "labels": [l["name"] for l in issue.get("labels", [])],
            })

        return {"tasks": tasks, "count": len(tasks), "state_filter": state}
    except Exception as e:
        return {"error": f"Failed to list tasks: {e}"}
