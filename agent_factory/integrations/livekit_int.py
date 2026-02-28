"""
LiveKit Integration
Real-time voice and video streaming for agent interactions.
Supports: room creation, token generation, participant management.
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def _livekit_available() -> bool:
    try:
        import livekit  # noqa
        return True
    except ImportError:
        return False


class LiveKitManager:
    """
    Manages LiveKit rooms and access tokens for voice/video agents.
    Requires LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET env vars.
    """

    def __init__(self):
        self.url = os.getenv("LIVEKIT_URL", "wss://your-livekit-server.com")
        self.api_key = os.getenv("LIVEKIT_API_KEY", "")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET", "")

    def _configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def create_room(self, room_name: str, empty_timeout: int = 300) -> Dict[str, Any]:
        """Create a LiveKit room."""
        if not self._configured():
            return {"error": "LiveKit not configured (LIVEKIT_API_KEY / LIVEKIT_API_SECRET missing)"}
        try:
            from livekit import api as lkapi
            client = lkapi.LiveKitAPI(url=self.url, api_key=self.api_key, api_secret=self.api_secret)
            import asyncio
            room = asyncio.run(client.room.create_room(
                lkapi.CreateRoomRequest(name=room_name, empty_timeout=empty_timeout)
            ))
            return {"room_name": room.name, "sid": room.sid, "url": self.url}
        except Exception as e:
            return {"error": str(e)}

    def generate_token(
        self,
        room_name: str,
        participant_name: str,
        identity: Optional[str] = None,
        can_publish: bool = True,
        can_subscribe: bool = True,
        ttl_seconds: int = 3600,
    ) -> Dict[str, Any]:
        """Generate an access token for a room participant."""
        if not self._configured():
            return {"error": "LiveKit not configured"}
        try:
            from livekit import api as lkapi
            token = (
                lkapi.AccessToken(self.api_key, self.api_secret)
                .with_identity(identity or participant_name)
                .with_name(participant_name)
                .with_grants(lkapi.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=can_publish,
                    can_subscribe=can_subscribe,
                ))
                .to_jwt()
            )
            return {
                "token": token,
                "room_name": room_name,
                "participant": participant_name,
                "livekit_url": self.url,
                "expires_in": ttl_seconds,
            }
        except Exception as e:
            return {"error": str(e)}

    def create_agent_session(
        self,
        agent_id: str,
        session_id: str,
        channel: str = "voice",
    ) -> Dict[str, Any]:
        """
        Create a full voice/video session: room + two tokens
        (one for user, one for agent).
        """
        room_name = f"agent-{agent_id[:8]}-{session_id}"
        room = self.create_room(room_name)
        if "error" in room:
            return room

        user_token = self.generate_token(room_name, "user", identity=f"user-{session_id}")
        agent_token = self.generate_token(
            room_name, f"agent-{agent_id[:8]}", identity=f"agent-{agent_id}",
            can_publish=True, can_subscribe=True,
        )

        return {
            "room": room,
            "channel": channel,
            "user_token": user_token.get("token"),
            "agent_token": agent_token.get("token"),
            "livekit_url": self.url,
            "session_id": session_id,
            "agent_id": agent_id,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "configured": self._configured(),
            "livekit_url": self.url,
            "available": _livekit_available(),
        }
