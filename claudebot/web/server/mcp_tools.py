"""MCP-style Tool Plugin System for Mimi.

Provides a lightweight way to register external tools via JSON config files.
This follows the Model Context Protocol (MCP) pattern where tools are
defined declaratively and loaded at startup.

Tools can be added by:
1. Placing a JSON file in the tools/ directory
2. Setting MCP_TOOLS_DIR env var to a custom directory
3. Programmatically via register_tool()

Each tool JSON file should have:
{
    "name": "tool_name",
    "description": "What the tool does",
    "input_schema": { ... JSON Schema ... },
    "handler": {
        "type": "http",
        "url": "https://api.example.com/endpoint",
        "method": "POST",
        "headers": { "Authorization": "Bearer ${ENV_VAR}" }
    }
}

Handler types:
- "http": Makes an HTTP request to the specified URL
- "command": Runs a shell command (disabled by default for security)
"""

import os
import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger("mimi-mcp")

_SERVER_DIR = Path(__file__).resolve().parent
TOOLS_DIR = os.getenv("MCP_TOOLS_DIR", str(_SERVER_DIR / "tools"))

# Registry of loaded tools
_tool_definitions: list[dict] = []
_tool_handlers: dict[str, callable] = {}


def _expand_env_vars(s: str) -> str:
    """Expand ${ENV_VAR} patterns in strings."""
    import re
    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, "")
    return re.sub(r'\$\{(\w+)\}', replacer, s)


def _make_http_handler(config: dict) -> callable:
    """Create an HTTP handler function from config."""
    url_template = config.get("url", "")
    method = config.get("method", "POST").upper()
    headers_template = config.get("headers", {})
    body_template = config.get("body_template", None)

    def handler(**kwargs):
        url = _expand_env_vars(url_template)
        headers = {k: _expand_env_vars(v) for k, v in headers_template.items()}

        if method == "GET":
            resp = httpx.get(url, params=kwargs, headers=headers, timeout=30)
        else:
            body = kwargs
            if body_template:
                body = json.loads(_expand_env_vars(json.dumps(body_template)))
                body.update(kwargs)
            resp = httpx.post(url, json=body, headers=headers, timeout=30)

        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"response": resp.text[:2000]}

    return handler


def register_tool(definition: dict, handler: callable = None):
    """Register a tool with its definition and handler."""
    name = definition.get("name")
    if not name:
        logger.warning("Tool definition missing 'name', skipping")
        return

    # If no handler provided, create one from handler config
    if handler is None and "handler" in definition:
        handler_config = definition["handler"]
        handler_type = handler_config.get("type", "http")

        if handler_type == "http":
            handler = _make_http_handler(handler_config)
        else:
            logger.warning("Unsupported handler type '%s' for tool '%s'", handler_type, name)
            return

    if handler is None:
        logger.warning("No handler for tool '%s', skipping", name)
        return

    # Clean definition for Claude API (remove handler config)
    clean_def = {k: v for k, v in definition.items() if k != "handler"}
    _tool_definitions.append(clean_def)
    _tool_handlers[name] = handler
    logger.info("Registered MCP tool: %s", name)


def load_tools_from_dir(directory: str = None):
    """Load tool definitions from JSON files in a directory."""
    tools_dir = Path(directory or TOOLS_DIR)
    if not tools_dir.exists():
        return

    for f in sorted(tools_dir.glob("*.json")):
        try:
            with open(f) as fh:
                definition = json.load(fh)

            if isinstance(definition, list):
                for d in definition:
                    register_tool(d)
            else:
                register_tool(definition)
        except Exception as e:
            logger.warning("Failed to load tool from %s: %s", f, e)


def get_tool_definitions() -> list[dict]:
    """Get all registered tool definitions (for Claude API)."""
    return list(_tool_definitions)


def get_tool_handlers() -> dict[str, callable]:
    """Get all registered tool handlers."""
    return dict(_tool_handlers)


# Auto-load tools on import
load_tools_from_dir()
