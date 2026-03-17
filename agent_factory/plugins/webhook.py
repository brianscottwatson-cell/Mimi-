"""
Plugin & Webhook Manager
Enables website embedding, outbound webhooks, and plugin extensibility.
"""
import os
import json
import hmac
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime


PLUGINS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plugins.json")


def _load_plugins() -> Dict[str, Any]:
    os.makedirs(os.path.dirname(PLUGINS_FILE), exist_ok=True)
    if os.path.exists(PLUGINS_FILE):
        try:
            with open(PLUGINS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_plugins(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(PLUGINS_FILE), exist_ok=True)
    with open(PLUGINS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


class WebhookManager:
    """
    Manages outbound webhooks: register, fire, verify signatures.
    Also generates embeddable widget snippets for websites.
    """

    def __init__(self):
        self._plugins: Dict[str, Any] = _load_plugins()

    def _persist(self):
        _save_plugins(self._plugins)

    # ------------------------------------------------------------------ #
    #  Webhook CRUD                                                        #
    # ------------------------------------------------------------------ #

    def register_webhook(
        self,
        agent_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        name: str = "",
    ) -> Dict[str, Any]:
        """Register an outbound webhook for an agent."""
        import secrets as sec
        wh_id = sec.token_urlsafe(8)
        webhook = {
            "id": wh_id,
            "agent_id": agent_id,
            "url": url,
            "events": events,  # e.g. ["message", "call", "sms"]
            "secret": secret or sec.token_urlsafe(24),
            "name": name or f"webhook-{wh_id}",
            "created_at": datetime.utcnow().isoformat(),
            "active": True,
            "delivery_log": [],
        }
        key = f"wh:{wh_id}"
        self._plugins[key] = webhook
        self._persist()
        return webhook

    def list_webhooks(self, agent_id: str) -> List[Dict[str, Any]]:
        return [
            v for k, v in self._plugins.items()
            if k.startswith("wh:") and v.get("agent_id") == agent_id
        ]

    def delete_webhook(self, webhook_id: str) -> bool:
        key = f"wh:{webhook_id}"
        if key in self._plugins:
            del self._plugins[key]
            self._persist()
            return True
        return False

    # ------------------------------------------------------------------ #
    #  Webhook firing                                                      #
    # ------------------------------------------------------------------ #

    def fire(
        self,
        agent_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Fire all matching webhooks for an agent event. Returns delivery results."""
        results = []
        for key, wh in self._plugins.items():
            if not key.startswith("wh:"):
                continue
            if wh.get("agent_id") != agent_id:
                continue
            if not wh.get("active"):
                continue
            if event_type not in wh.get("events", []):
                continue

            result = self._deliver(wh, event_type, payload)
            results.append(result)

            # Log delivery
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event_type,
                "status": result.get("status"),
                "http_code": result.get("http_code"),
            }
            wh.setdefault("delivery_log", []).append(log_entry)
            wh["delivery_log"] = wh["delivery_log"][-50:]  # keep last 50
            self._persist()

        return results

    def _deliver(self, webhook: Dict[str, Any], event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP POST the payload to the webhook URL."""
        try:
            import httpx
            body = json.dumps({
                "event": event_type,
                "agent_id": webhook["agent_id"],
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload,
            })
            sig = self._sign(body, webhook["secret"])
            resp = httpx.post(
                webhook["url"],
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-AgentFactory-Signature": sig,
                    "X-AgentFactory-Event": event_type,
                },
                timeout=10,
            )
            return {"status": "delivered", "http_code": resp.status_code, "url": webhook["url"]}
        except Exception as e:
            return {"status": "failed", "error": str(e), "url": webhook["url"]}

    def _sign(self, body: str, secret: str) -> str:
        """HMAC-SHA256 signature for webhook payload verification."""
        return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()  # noqa: E501 (hmac.new is correct for Python stdlib)

    def verify_signature(self, body: str, secret: str, signature: str) -> bool:
        expected = self._sign(body, secret)
        return hmac.compare_digest(expected, signature)

    # ------------------------------------------------------------------ #
    #  Website embed widget                                                #
    # ------------------------------------------------------------------ #

    def generate_embed_snippet(
        self,
        agent_id: str,
        api_base_url: str,
        theme: str = "dark",
        position: str = "bottom-right",
        title: str = "Chat with AI",
    ) -> str:
        """
        Generate a JavaScript snippet for embedding the agent chat widget
        on any website. Drop this <script> tag into any HTML page.
        """
        return f"""<!-- Agent Factory Widget — paste before </body> -->
<script>
(function() {{
  var AGENT_ID = "{agent_id}";
  var API_URL  = "{api_base_url}";
  var THEME    = "{theme}";
  var POSITION = "{position}";
  var TITLE    = "{title}";

  var style = document.createElement("style");
  style.textContent = [
    "#af-widget-btn{{position:fixed;{self._pos_css(position)}z-index:9999;",
    "width:56px;height:56px;border-radius:50%;background:#7c3aed;",
    "border:none;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);",
    "font-size:24px;color:#fff;}}",
    "#af-widget-frame{{position:fixed;{self._frame_css(position)}z-index:9998;",
    "width:370px;height:520px;border:none;border-radius:16px;",
    "box-shadow:0 8px 30px rgba(0,0,0,.35);display:none;}}",
  ].join("");
  document.head.appendChild(style);

  var btn   = document.createElement("button");
  btn.id    = "af-widget-btn";
  btn.title = TITLE;
  btn.innerHTML = "&#x1F4AC;";
  document.body.appendChild(btn);

  var frame  = document.createElement("iframe");
  frame.id   = "af-widget-frame";
  frame.src  = API_URL + "/widget/" + AGENT_ID + "?theme=" + THEME;
  frame.allow = "microphone";
  document.body.appendChild(frame);

  var open = false;
  btn.addEventListener("click", function() {{
    open = !open;
    frame.style.display = open ? "block" : "none";
    btn.innerHTML = open ? "&#x2715;" : "&#x1F4AC;";
  }});
}})();
</script>"""

    def _pos_css(self, position: str) -> str:
        positions = {
            "bottom-right": "bottom:24px;right:24px;",
            "bottom-left": "bottom:24px;left:24px;",
            "top-right": "top:24px;right:24px;",
            "top-left": "top:24px;left:24px;",
        }
        return positions.get(position, "bottom:24px;right:24px;")

    def _frame_css(self, position: str) -> str:
        positions = {
            "bottom-right": "bottom:92px;right:24px;",
            "bottom-left": "bottom:92px;left:24px;",
            "top-right": "top:92px;right:24px;",
            "top-left": "top:92px;left:24px;",
        }
        return positions.get(position, "bottom:92px;right:24px;")
