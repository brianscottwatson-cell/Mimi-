"""
Analytics Tracker
Tracks agent interactions, latency, token usage, and channel activity.
Stores locally (JSON) with optional ELK/Elasticsearch shipping.
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


ANALYTICS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "analytics.json")


def _ensure_data_dir():
    os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)


def _load_events() -> List[Dict[str, Any]]:
    _ensure_data_dir()
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_events(events: List[Dict[str, Any]]):
    _ensure_data_dir()
    # Keep last 10,000 events
    events = events[-10000:]
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(events, f, default=str)


class AnalyticsTracker:
    """
    Records and queries platform analytics.
    Optional: ships events to Elasticsearch (ELK stack) if configured.
    """

    def __init__(self):
        self._events: List[Dict[str, Any]] = _load_events()
        self._elk_url = os.getenv("ELASTICSEARCH_URL")

    # ------------------------------------------------------------------ #
    #  Event recording                                                     #
    # ------------------------------------------------------------------ #

    def record(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "id": f"{int(time.time()*1000)}-{len(self._events)}",
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        self._events.append(event)
        _save_events(self._events)

        # Optionally ship to ELK
        if self._elk_url:
            self._ship_to_elk(event)

        return event

    def record_chat(
        self,
        agent_id: str,
        session_id: str,
        channel: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0,
        provider: str = "",
        model: str = "",
        error: Optional[str] = None,
    ):
        return self.record("chat", {
            "agent_id": agent_id,
            "session_id": session_id,
            "channel": channel,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "provider": provider,
            "model": model,
            "error": error,
        })

    def record_call(self, agent_id: str, call_sid: str, direction: str, duration_s: int = 0):
        return self.record("call", {
            "agent_id": agent_id,
            "call_sid": call_sid,
            "direction": direction,
            "duration_seconds": duration_s,
        })

    def record_sms(self, agent_id: str, message_sid: str, direction: str):
        return self.record("sms", {
            "agent_id": agent_id,
            "message_sid": message_sid,
            "direction": direction,
        })

    def record_image_gen(self, agent_id: str, prompt: str, model: str, count: int = 1):
        return self.record("image_generation", {
            "agent_id": agent_id,
            "prompt": prompt[:200],
            "model": model,
            "image_count": count,
        })

    # ------------------------------------------------------------------ #
    #  Queries                                                             #
    # ------------------------------------------------------------------ #

    def get_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        filtered = [
            e for e in self._events
            if e.get("timestamp", "") >= cutoff
            and (not agent_id or e.get("agent_id") == agent_id)
            and (not event_type or e.get("type") == event_type)
        ]
        return filtered[-limit:]

    def summary(self, agent_id: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        events = self.get_events(agent_id=agent_id, hours=hours, limit=10000)

        chat_events = [e for e in events if e["type"] == "chat"]
        call_events = [e for e in events if e["type"] == "call"]
        sms_events = [e for e in events if e["type"] == "sms"]
        img_events = [e for e in events if e["type"] == "image_generation"]

        total_tokens = sum(e.get("total_tokens", 0) for e in chat_events)
        avg_latency = (
            sum(e.get("latency_ms", 0) for e in chat_events) / len(chat_events)
            if chat_events else 0
        )
        errors = [e for e in chat_events if e.get("error")]

        # Channel breakdown
        channels: Dict[str, int] = defaultdict(int)
        for e in chat_events:
            channels[e.get("channel", "chat")] += 1

        # Provider breakdown
        providers: Dict[str, int] = defaultdict(int)
        for e in chat_events:
            providers[e.get("provider", "unknown")] += 1

        return {
            "period_hours": hours,
            "agent_id": agent_id or "all",
            "chat": {
                "total_interactions": len(chat_events),
                "total_tokens": total_tokens,
                "avg_latency_ms": round(avg_latency, 1),
                "error_count": len(errors),
                "by_channel": dict(channels),
                "by_provider": dict(providers),
            },
            "calls": {
                "total": len(call_events),
                "total_duration_s": sum(e.get("duration_seconds", 0) for e in call_events),
            },
            "sms": {"total": len(sms_events)},
            "image_gen": {"total": len(img_events)},
        }

    # ------------------------------------------------------------------ #
    #  ELK shipping                                                        #
    # ------------------------------------------------------------------ #

    def _ship_to_elk(self, event: Dict[str, Any]):
        """Ship event to Elasticsearch index."""
        try:
            import httpx
            url = f"{self._elk_url}/agent-factory-events/_doc"
            httpx.post(url, json=event, timeout=2)
        except Exception:
            pass  # ELK shipping is best-effort
