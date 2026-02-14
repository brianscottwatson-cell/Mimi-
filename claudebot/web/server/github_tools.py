"""GitHub repository file tools for Mimi.

Provides CRUD operations on files in the brianscottwatson-cell/Mimi- repo
via the GitHub REST API (Contents endpoint). Files are served as GitHub Pages.
"""

import os
import base64
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_OWNER = "brianscottwatson-cell"
GITHUB_REPO = "Mimi-"
GITHUB_BRANCH = "main"
GITHUB_API = "https://api.github.com"

GITHUB_AVAILABLE = bool(GITHUB_TOKEN)

# ---------------------------------------------------------------------------
# Safety: Path blocklist and extension allowlist
# ---------------------------------------------------------------------------

BLOCKED_PATHS = {
    "claudebot/web/server/app.py",
    "claudebot/web/server/mimi_core.py",
    "claudebot/web/server/google_services.py",
    "claudebot/web/server/google_auth.py",
    "claudebot/web/server/web_search.py",
    "claudebot/web/server/telegram_bot.py",
    "claudebot/web/server/start_railway.py",
    "claudebot/web/server/github_tools.py",
    "claudebot/web/server/requirements.txt",
    "railway.json",
    ".env",
    ".gitignore",
}

ALLOWED_EXTENSIONS = {
    ".html", ".css", ".js", ".json", ".md", ".txt",
    ".svg", ".xml", ".yaml", ".yml", ".csv",
}


def _headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _validate_path(path):
    """Validate a file path against safety rules. Returns (ok, error_msg)."""
    path = path.strip().lstrip("/")
    if not path:
        return False, "Empty path"
    if path in BLOCKED_PATHS:
        return False, f"BLOCKED: '{path}' is a protected infrastructure file and cannot be modified."
    ext = os.path.splitext(path)[1].lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
    return True, ""


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def github_list_files(path="", recursive=False):
    """List files and directories at a given path in the repo."""
    path = path.strip().lstrip("/")
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"

    resp = requests.get(url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
    if resp.status_code == 404:
        return {"error": f"Path '{path}' not found in repo."}
    resp.raise_for_status()

    data = resp.json()
    if isinstance(data, dict):
        return {"type": "file", "name": data["name"], "path": data["path"],
                "size": data.get("size", 0), "sha": data["sha"]}

    items = []
    for item in data:
        items.append({
            "name": item["name"],
            "path": item["path"],
            "type": item["type"],
            "size": item.get("size", 0),
        })

    if recursive:
        for d in [i for i in items if i["type"] == "dir"]:
            sub_url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{d['path']}"
            try:
                sub_resp = requests.get(sub_url, headers=_headers(),
                                        params={"ref": GITHUB_BRANCH}, timeout=15)
                if sub_resp.status_code == 200:
                    sub_data = sub_resp.json()
                    if isinstance(sub_data, list):
                        for si in sub_data:
                            items.append({
                                "name": si["name"],
                                "path": si["path"],
                                "type": si["type"],
                                "size": si.get("size", 0),
                            })
            except Exception:
                pass

    return {"path": path or "/", "items": items, "count": len(items)}


def github_read_file(path):
    """Read a file from the repo. Returns decoded content and SHA."""
    path = path.strip().lstrip("/")
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"

    resp = requests.get(url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
    if resp.status_code == 404:
        return {"error": f"File '{path}' not found."}
    resp.raise_for_status()

    data = resp.json()
    if data.get("type") != "file":
        return {"error": f"'{path}' is a directory. Use github_list_files instead."}

    content = base64.b64decode(data["content"]).decode("utf-8")
    truncated = len(content) > 15000
    if truncated:
        content = content[:15000] + f"\n... [TRUNCATED — file is {data['size']} bytes total]"

    return {
        "path": data["path"],
        "sha": data["sha"],
        "size": data["size"],
        "content": content,
        "truncated": truncated,
    }


def github_create_file(path, content, commit_message=None):
    """Create a new file in the repo. Fails if file already exists."""
    path = path.strip().lstrip("/")
    ok, err = _validate_path(path)
    if not ok:
        return {"error": err}

    check_url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    check = requests.get(check_url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=10)
    if check.status_code == 200:
        return {"error": f"File '{path}' already exists. Use github_update_file to modify it."}

    if not commit_message:
        commit_message = f"Create {path} via Mimi"

    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": GITHUB_BRANCH,
    }

    resp = requests.put(url, headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    pages_url = f"https://{GITHUB_OWNER}.github.io/{GITHUB_REPO}/{path}"

    return {
        "status": "created",
        "path": data["content"]["path"],
        "sha": data["content"]["sha"],
        "commit": data["commit"]["sha"][:7],
        "pages_url": pages_url,
    }


def github_update_file(path, content, commit_message=None, sha=None):
    """Update an existing file. Auto-fetches SHA if not provided."""
    path = path.strip().lstrip("/")
    ok, err = _validate_path(path)
    if not ok:
        return {"error": err}

    if not sha:
        read_result = github_read_file(path)
        if "error" in read_result:
            return {"error": f"Cannot update — {read_result['error']}. Use github_create_file for new files."}
        sha = read_result["sha"]

    if not commit_message:
        commit_message = f"Update {path} via Mimi"

    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
        "branch": GITHUB_BRANCH,
    }

    resp = requests.put(url, headers=_headers(), json=payload, timeout=20)
    if resp.status_code == 409:
        return {"error": "Conflict — file was modified since SHA was read. Re-read the file and try again."}
    resp.raise_for_status()

    data = resp.json()
    pages_url = f"https://{GITHUB_OWNER}.github.io/{GITHUB_REPO}/{path}"

    return {
        "status": "updated",
        "path": data["content"]["path"],
        "sha": data["content"]["sha"],
        "commit": data["commit"]["sha"][:7],
        "pages_url": pages_url,
    }


def github_delete_file(path, commit_message=None, sha=None):
    """Delete a file from the repo."""
    path = path.strip().lstrip("/")
    ok, err = _validate_path(path)
    if not ok:
        return {"error": err}

    if not sha:
        read_result = github_read_file(path)
        if "error" in read_result:
            return {"error": f"Cannot delete — {read_result['error']}"}
        sha = read_result["sha"]

    if not commit_message:
        commit_message = f"Delete {path} via Mimi"

    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    payload = {
        "message": commit_message,
        "sha": sha,
        "branch": GITHUB_BRANCH,
    }

    resp = requests.delete(url, headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()

    return {
        "status": "deleted",
        "path": path,
        "commit": resp.json()["commit"]["sha"][:7],
    }


def github_get_pages_status():
    """Get GitHub Pages status and recent commits."""
    result = {"repo": f"{GITHUB_OWNER}/{GITHUB_REPO}", "branch": GITHUB_BRANCH}

    pages_url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pages"
    try:
        resp = requests.get(pages_url, headers=_headers(), timeout=10)
        if resp.status_code == 200:
            pages = resp.json()
            result["pages"] = {
                "url": pages.get("html_url", ""),
                "status": pages.get("status", "unknown"),
            }
        else:
            result["pages"] = {"status": "not_configured_or_private"}
    except Exception as e:
        result["pages"] = {"error": str(e)}

    commits_url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits"
    try:
        resp = requests.get(commits_url, headers=_headers(),
                            params={"sha": GITHUB_BRANCH, "per_page": 5}, timeout=10)
        resp.raise_for_status()
        result["recent_commits"] = [
            {"sha": c["sha"][:7], "message": c["commit"]["message"],
             "date": c["commit"]["committer"]["date"]}
            for c in resp.json()
        ]
    except Exception as e:
        result["recent_commits_error"] = str(e)

    return result
