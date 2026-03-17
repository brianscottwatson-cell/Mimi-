"""
Dynamic loader for Mimi's custom tools.

Each .py file in this directory (except __init__.py and _-prefixed files) must export:
    TOOLS: list[dict]         — Claude tool JSON schemas
    HANDLERS: dict[str, callable] — {tool_name: handler_function}

Broken modules are skipped with a warning.
"""

import importlib
import os
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_custom_tools():
    """Scan this directory for tool modules. Returns (tools_list, handlers_dict)."""
    all_tools = []
    all_handlers = {}

    for filename in sorted(os.listdir(_THIS_DIR)):
        if not filename.endswith(".py") or filename.startswith("_") or filename == "__init__.py":
            continue

        module_name = filename[:-3]
        module_path = f"custom_tools.{module_name}"

        try:
            mod = importlib.import_module(module_path)
            tools = getattr(mod, "TOOLS", None)
            handlers = getattr(mod, "HANDLERS", None)

            if not isinstance(tools, list) or not isinstance(handlers, dict):
                print(f"[custom_tools] SKIP {filename}: missing TOOLS list or HANDLERS dict", flush=True)
                continue

            # Validate every tool has a handler
            missing = [t["name"] for t in tools if t.get("name") not in handlers]
            if missing:
                print(f"[custom_tools] SKIP {filename}: tools missing handlers: {missing}", flush=True)
                continue

            all_tools.extend(tools)
            all_handlers.update(handlers)
            print(f"[custom_tools] Loaded {filename}: {[t['name'] for t in tools]}", flush=True)

        except Exception:
            print(f"[custom_tools] ERROR loading {filename}:", flush=True)
            traceback.print_exc()

    return all_tools, all_handlers
