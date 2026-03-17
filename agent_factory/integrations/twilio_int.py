"""
Twilio Integration
Handles: SMS messaging, voice calls, call recording, transcription,
         call scheduling, and Media Streams for real-time audio.
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


def _get_client():
    try:
        from twilio.rest import Client
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        if not sid or not token:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required")
        return Client(sid, token)
    except ImportError:
        raise RuntimeError("twilio package required: pip install twilio")


TWILIO_PHONE = lambda: os.getenv("TWILIO_PHONE_NUMBER", "")


class TwilioSMS:
    """Send and receive SMS messages via Twilio."""

    def send(self, to: str, body: str, from_: Optional[str] = None) -> Dict[str, Any]:
        try:
            client = _get_client()
            msg = client.messages.create(
                body=body,
                from_=from_ or TWILIO_PHONE(),
                to=to,
            )
            return {
                "status": "sent",
                "sid": msg.sid,
                "to": to,
                "from": msg.from_,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def list_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            client = _get_client()
            messages = client.messages.list(limit=limit)
            return [
                {
                    "sid": m.sid,
                    "from": m.from_,
                    "to": m.to,
                    "body": m.body,
                    "status": m.status,
                    "date_sent": str(m.date_sent),
                }
                for m in messages
            ]
        except Exception as e:
            return [{"error": str(e)}]


class TwilioVoice:
    """
    Twilio voice call management.
    Supports outbound calls with TwiML, call recording, and transcription hooks.
    """

    def make_call(
        self,
        to: str,
        twiml_url: str,
        from_: Optional[str] = None,
        record: bool = True,
    ) -> Dict[str, Any]:
        """Initiate an outbound call."""
        try:
            client = _get_client()
            call = client.calls.create(
                to=to,
                from_=from_ or TWILIO_PHONE(),
                url=twiml_url,
                record=record,
            )
            return {
                "status": "initiated",
                "call_sid": call.sid,
                "to": to,
                "from": call.from_formatted,
                "recording": record,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def hangup(self, call_sid: str) -> Dict[str, Any]:
        try:
            client = _get_client()
            call = client.calls(call_sid).update(status="completed")
            return {"status": "ended", "call_sid": call_sid}
        except Exception as e:
            return {"error": str(e)}

    def list_calls(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            client = _get_client()
            calls = client.calls.list(limit=limit)
            return [
                {
                    "sid": c.sid,
                    "from": c.from_formatted,
                    "to": c.to_formatted,
                    "status": c.status,
                    "duration": c.duration,
                    "start_time": str(c.start_time),
                }
                for c in calls
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def get_recordings(self, call_sid: str) -> List[Dict[str, Any]]:
        try:
            client = _get_client()
            recordings = client.recordings.list(call_sid=call_sid)
            return [
                {
                    "sid": r.sid,
                    "duration": r.duration,
                    "url": f"https://api.twilio.com{r.uri.replace('.json', '.mp3')}",
                    "date_created": str(r.date_created),
                }
                for r in recordings
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def transcribe_recording(self, recording_url: str, callback_url: str) -> Dict[str, Any]:
        """
        Submit a recording for transcription.
        Twilio calls callback_url when transcription is ready.
        """
        try:
            client = _get_client()
            transcription = client.transcriptions.create(
                recording_url=recording_url,
                transcribe_callback=callback_url,
            )
            return {
                "status": "queued",
                "transcription_sid": transcription.sid,
            }
        except Exception as e:
            return {"error": str(e)}


class TwilioMediaStream:
    """
    Twilio Media Streams — real-time audio streaming for voice AI.
    Generates TwiML for websocket-based audio capture.
    """

    def generate_stream_twiml(
        self,
        websocket_url: str,
        say_text: str = "Connecting you to your AI agent.",
    ) -> str:
        """
        Return TwiML that streams call audio to a websocket endpoint.
        The websocket receives raw audio and can stream AI responses back.
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{say_text}</Say>
    <Connect>
        <Stream url="{websocket_url}">
            <Parameter name="source" value="twilio_media_stream"/>
        </Stream>
    </Connect>
</Response>"""

    def generate_gather_twiml(
        self,
        action_url: str,
        say_text: str = "How can I help you today?",
        input_types: str = "speech dtmf",
        timeout: int = 5,
    ) -> str:
        """TwiML for gathering speech/DTMF input and posting to action_url."""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="{input_types}" timeout="{timeout}" action="{action_url}" method="POST">
        <Say>{say_text}</Say>
    </Gather>
    <Say>We did not receive your input. Goodbye.</Say>
    <Hangup/>
</Response>"""


class TwilioScheduler:
    """
    Schedule outbound calls/SMS for future delivery.
    Uses Twilio's MessageScheduling / Call scheduling features.
    """

    def schedule_sms(
        self,
        to: str,
        body: str,
        send_at: str,  # ISO 8601
        from_: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            client = _get_client()
            msg = client.messages.create(
                body=body,
                from_=from_ or TWILIO_PHONE(),
                to=to,
                schedule_type="fixed",
                send_at=send_at,
                messaging_service_sid=os.getenv("TWILIO_MESSAGING_SID", ""),
            )
            return {"status": "scheduled", "sid": msg.sid, "send_at": send_at}
        except Exception as e:
            return {"error": str(e)}
