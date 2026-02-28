"""
Agent Registry — stores, retrieves, and manages all agent configurations.
Uses an in-memory store with JSON persistence.
"""
import os
import json
import uuid
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime


REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "agent_registry.json")


def _ensure_data_dir():
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)


def _load_registry() -> Dict[str, Any]:
    _ensure_data_dir()
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_registry(data: Dict[str, Any]):
    _ensure_data_dir()
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


class AgentRegistry:
    """
    Central registry for all Agent Factory agents.
    Each agent has a unique ID and API key for secure access.
    """

    def __init__(self):
        self._agents: Dict[str, Any] = _load_registry()

    def _persist(self):
        _save_registry(self._agents)

    # ------------------------------------------------------------------ #
    #  CRUD                                                                #
    # ------------------------------------------------------------------ #

    def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent and return its full record with ID and key."""
        agent_id = str(uuid.uuid4())
        api_key = secrets.token_urlsafe(32)

        record = {
            "id": agent_id,
            "api_key": api_key,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active",
            **config,
        }
        # Ensure required defaults
        record.setdefault("name", f"Agent-{agent_id[:8]}")
        record.setdefault("description", "")
        record.setdefault("llm_provider", "anthropic")
        record.setdefault("llm_model", "claude-sonnet-4-6")
        record.setdefault("channels", ["chat"])
        record.setdefault("tools", [])
        record.setdefault("soul", None)
        record.setdefault("rag_enabled", False)
        record.setdefault("rag_namespace", agent_id)
        record.setdefault("system_prompt", "")
        record.setdefault("plugins", [])
        record.setdefault("analytics_enabled", True)
        record.setdefault("twilio_enabled", False)
        record.setdefault("livekit_enabled", False)

        self._agents[agent_id] = record
        self._persist()
        return record

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def get_agent_by_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        for agent in self._agents.values():
            if agent.get("api_key") == api_key:
                return agent
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return all agents (sans api_key for security)."""
        safe = []
        for a in self._agents.values():
            copy = dict(a)
            copy.pop("api_key", None)
            safe.append(copy)
        return safe

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if agent_id not in self._agents:
            return None
        updates.pop("id", None)
        updates.pop("api_key", None)
        updates.pop("created_at", None)
        self._agents[agent_id].update(updates)
        self._agents[agent_id]["updated_at"] = datetime.utcnow().isoformat()
        self._persist()
        return self._agents[agent_id]

    def delete_agent(self, agent_id: str) -> bool:
        if agent_id not in self._agents:
            return False
        del self._agents[agent_id]
        self._persist()
        return True

    def rotate_key(self, agent_id: str) -> Optional[str]:
        if agent_id not in self._agents:
            return None
        new_key = secrets.token_urlsafe(32)
        self._agents[agent_id]["api_key"] = new_key
        self._agents[agent_id]["updated_at"] = datetime.utcnow().isoformat()
        self._persist()
        return new_key

    # ------------------------------------------------------------------ #
    #  Soul / RAG helpers                                                  #
    # ------------------------------------------------------------------ #

    def attach_soul(self, agent_id: str, soul_content: str) -> bool:
        if agent_id not in self._agents:
            return False
        self._agents[agent_id]["soul"] = soul_content
        self._agents[agent_id]["updated_at"] = datetime.utcnow().isoformat()
        self._persist()
        return True

    def attach_tools(self, agent_id: str, tools: List[str]) -> bool:
        if agent_id not in self._agents:
            return False
        existing = self._agents[agent_id].get("tools", [])
        merged = list(set(existing + tools))
        self._agents[agent_id]["tools"] = merged
        self._agents[agent_id]["updated_at"] = datetime.utcnow().isoformat()
        self._persist()
        return True
