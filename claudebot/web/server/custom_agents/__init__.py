"""
Dynamic loader for Mimi's custom agent definitions.

Each .py file in this directory (except __init__.py and _-prefixed files) must export:
    AGENTS: list[dict]  — each with keys: name, role, description

These get injected into the system prompt so Mimi knows about them.
"""

import importlib
import os
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_custom_agents():
    """Scan this directory for agent definition modules. Returns list of agent dicts."""
    all_agents = []

    for filename in sorted(os.listdir(_THIS_DIR)):
        if not filename.endswith(".py") or filename.startswith("_") or filename == "__init__.py":
            continue

        module_name = filename[:-3]
        module_path = f"custom_agents.{module_name}"

        try:
            mod = importlib.import_module(module_path)
            agents = getattr(mod, "AGENTS", None)

            if not isinstance(agents, list):
                print(f"[custom_agents] SKIP {filename}: missing AGENTS list", flush=True)
                continue

            valid = []
            for a in agents:
                if all(k in a for k in ("name", "role", "description")):
                    valid.append(a)
                else:
                    print(f"[custom_agents] SKIP agent in {filename}: missing name/role/description", flush=True)

            all_agents.extend(valid)
            print(f"[custom_agents] Loaded {filename}: {[a['name'] for a in valid]}", flush=True)

        except Exception:
            print(f"[custom_agents] ERROR loading {filename}:", flush=True)
            traceback.print_exc()

    return all_agents
