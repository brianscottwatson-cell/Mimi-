"""
Agent Factory — creates and runs configured agents.
Bridges registry configs to live LLM sessions with RAG, soul, and tool support.
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from agent_factory.registry import AgentRegistry
from agent_factory.soul import parse_soul, build_system_prompt_from_soul
from agent_factory.rag import RAGManager
from agent_factory.integrations.llm_switch import LLMRouter


class AgentFactory:
    """
    Orchestrates agent creation, configuration, and live chat sessions.
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.rag = RAGManager()
        self.router = LLMRouter()
        # Active sessions: agent_id -> list of messages
        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    # ------------------------------------------------------------------ #
    #  Agent CRUD (delegate to registry)                                   #
    # ------------------------------------------------------------------ #

    def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.registry.create_agent(config)

        # If soul content provided, parse and update system prompt
        soul_content = config.get("soul")
        if soul_content:
            soul = parse_soul(soul_content)
            enhanced_prompt = build_system_prompt_from_soul(soul, config.get("system_prompt", ""))
            self.registry.update_agent(agent["id"], {"system_prompt": enhanced_prompt})
            agent["system_prompt"] = enhanced_prompt

        # If RAG docs provided at creation, ingest them
        rag_docs = config.get("rag_documents", [])
        if rag_docs and agent.get("rag_enabled"):
            self.rag.ingest_documents(agent["rag_namespace"], rag_docs)

        return agent

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self.registry.get_agent(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        return self.registry.list_agents()

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Re-apply soul if updated
        if "soul" in updates and updates["soul"]:
            soul = parse_soul(updates["soul"])
            existing = self.registry.get_agent(agent_id) or {}
            enhanced = build_system_prompt_from_soul(soul, existing.get("system_prompt", ""))
            updates["system_prompt"] = enhanced
        return self.registry.update_agent(agent_id, updates)

    def delete_agent(self, agent_id: str) -> bool:
        # Clean up sessions
        self._sessions.pop(agent_id, None)
        return self.registry.delete_agent(agent_id)

    # ------------------------------------------------------------------ #
    #  Chat                                                                #
    # ------------------------------------------------------------------ #

    def chat(
        self,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
        channel: str = "chat",
    ) -> Dict[str, Any]:
        """
        Send a message to a configured agent.
        Handles RAG context injection, LLM routing, and session history.
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}

        key = f"{agent_id}:{session_id or 'default'}"
        history = self._sessions.setdefault(key, [])

        # Build system prompt (with optional RAG context)
        system_prompt = agent.get("system_prompt", "You are a helpful assistant.")
        if agent.get("rag_enabled"):
            context = self.rag.build_context(agent["rag_namespace"], message)
            if context:
                system_prompt = f"{system_prompt}\n\n{context}"

        # Add user message
        history.append({"role": "user", "content": message})

        # Route to appropriate LLM
        response_text = self.router.complete(
            provider=agent.get("llm_provider", "anthropic"),
            model=agent.get("llm_model", "claude-sonnet-4-6"),
            system_prompt=system_prompt,
            messages=history,
            max_tokens=agent.get("max_tokens", 2048),
        )

        # Store assistant response
        history.append({"role": "assistant", "content": response_text})

        # Trim history (keep last 50 pairs)
        if len(history) > 100:
            self._sessions[key] = history[-100:]

        return {
            "agent_id": agent_id,
            "agent_name": agent.get("name", "Agent"),
            "response": response_text,
            "session_id": session_id or "default",
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat(),
            "rag_used": agent.get("rag_enabled", False),
            "llm_provider": agent.get("llm_provider"),
            "llm_model": agent.get("llm_model"),
        }

    def reset_session(self, agent_id: str, session_id: str = "default"):
        key = f"{agent_id}:{session_id}"
        self._sessions.pop(key, None)

    # ------------------------------------------------------------------ #
    #  RAG management                                                      #
    # ------------------------------------------------------------------ #

    def ingest_documents(self, agent_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        namespace = agent.get("rag_namespace", agent_id)
        ids = self.rag.ingest_documents(namespace, documents)
        # Auto-enable RAG if not already
        if not agent.get("rag_enabled"):
            self.registry.update_agent(agent_id, {"rag_enabled": True})
        return {"ingested_chunks": len(ids), "namespace": namespace}

    def rag_stats(self, agent_id: str) -> Dict[str, Any]:
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        return self.rag.stats(agent.get("rag_namespace", agent_id))

    def list_rag_documents(self, agent_id: str) -> List[Dict[str, Any]]:
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return []
        return self.rag.list_documents(agent.get("rag_namespace", agent_id))

    # ------------------------------------------------------------------ #
    #  Soul management                                                     #
    # ------------------------------------------------------------------ #

    def upload_soul(self, agent_id: str, soul_content: str) -> Dict[str, Any]:
        from agent_factory.soul import validate_soul
        validation = validate_soul(soul_content)
        if not validation["valid"]:
            return {"error": "Soul validation failed", "warnings": validation["warnings"]}

        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        soul = validation["parsed"]
        enhanced_prompt = build_system_prompt_from_soul(soul, agent.get("system_prompt", ""))
        self.registry.update_agent(agent_id, {
            "soul": soul_content,
            "system_prompt": enhanced_prompt,
            "name": soul.get("name") or agent.get("name"),
        })
        return {"status": "ok", "parsed": soul, "warnings": validation["warnings"]}

    # ------------------------------------------------------------------ #
    #  LLM switching                                                       #
    # ------------------------------------------------------------------ #

    def switch_llm(self, agent_id: str, provider: str, model: str) -> Dict[str, Any]:
        if not self.router.is_supported(provider):
            return {"error": f"Provider '{provider}' not supported"}
        result = self.registry.update_agent(agent_id, {"llm_provider": provider, "llm_model": model})
        if not result:
            return {"error": "Agent not found"}
        return {"status": "switched", "provider": provider, "model": model}

    def list_providers(self) -> Dict[str, Any]:
        return self.router.list_providers()
