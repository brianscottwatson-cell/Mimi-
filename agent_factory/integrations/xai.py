"""
xAI Grok Integration
Supports: chat, image generation (Grok Imagine), real-time search,
          vision (image understanding), and future video/audio hooks.
"""
import os
from typing import Dict, Any, Optional, List


XAI_BASE_URL = "https://api.x.ai/v1"


def _get_client():
    try:
        import openai
        key = os.getenv("XAI_API_KEY")
        if not key:
            raise ValueError("XAI_API_KEY not set")
        return openai.OpenAI(api_key=key, base_url=XAI_BASE_URL)
    except ImportError:
        raise RuntimeError("openai package required for xAI integration")


class GrokChat:
    """Grok chat completions with optional real-time search grounding."""

    def __init__(self, model: str = "grok-2"):
        self.model = model

    def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        enable_search: bool = False,
    ) -> Dict[str, Any]:
        client = _get_client()
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Enable real-time web search grounding if requested
        if enable_search:
            kwargs["tools"] = [{"type": "web_search"}]

        try:
            resp = client.chat.completions.create(**kwargs)
            text = resp.choices[0].message.content
            return {
                "text": text,
                "model": self.model,
                "usage": {
                    "prompt_tokens": resp.usage.prompt_tokens,
                    "completion_tokens": resp.usage.completion_tokens,
                } if resp.usage else {},
                "search_used": enable_search,
            }
        except Exception as e:
            return {"error": str(e), "model": self.model}


class GrokVision:
    """Grok vision — send images + text for multimodal understanding."""

    def __init__(self, model: str = "grok-2-vision-1212"):
        self.model = model

    def analyze(
        self,
        text: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        media_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        client = _get_client()

        content: List[Dict[str, Any]] = [{"type": "text", "text": text}]

        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_base64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_base64}"},
            })

        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=2048,
            )
            return {"text": resp.choices[0].message.content, "model": self.model}
        except Exception as e:
            return {"error": str(e)}


class GrokImageGen:
    """
    Grok Imagine — text-to-image generation.
    Uses the /images/generations endpoint on xAI's API.
    """

    def __init__(self, model: str = "grok-2-image-1212"):
        self.model = model

    def generate(
        self,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url",
    ) -> Dict[str, Any]:
        client = _get_client()
        try:
            resp = client.images.generate(
                model=self.model,
                prompt=prompt,
                n=n,
                size=size,
                response_format=response_format,
            )
            images = []
            for img in resp.data:
                if response_format == "url":
                    images.append({"url": img.url})
                else:
                    images.append({"b64_json": img.b64_json})
            return {"images": images, "model": self.model, "prompt": prompt}
        except Exception as e:
            return {"error": str(e), "model": self.model}


class GrokSearch:
    """
    Real-time web search via Grok's search-enabled chat.
    Provides up-to-date information from X (Twitter) and the web.
    """

    def __init__(self, model: str = "grok-2"):
        self.chat = GrokChat(model=model)

    def search(self, query: str) -> Dict[str, Any]:
        return self.chat.complete(
            messages=[{"role": "user", "content": query}],
            system_prompt="You are a real-time search assistant. Search the web and X for the most current information.",
            enable_search=True,
        )


# ------------------------------------------------------------------ #
#  Future hooks for Grok 5 / Grok Imagine video                       #
# ------------------------------------------------------------------ #

class GrokVideoGen:
    """
    Placeholder for Grok Imagine video generation API.
    Will support text-to-video, image-to-video, and video editing.
    Async job-based: submit → poll → retrieve.
    """

    def submit_job(
        self,
        prompt: str,
        duration_seconds: int = 15,
        style: Optional[str] = None,
    ) -> Dict[str, Any]:
        # TODO: Implement when Grok Imagine video API is released
        return {
            "status": "pending",
            "message": "Grok Imagine Video API integration coming in Grok 5 / 2026 release.",
            "prompt": prompt,
            "duration": duration_seconds,
        }

    def poll_job(self, job_id: str) -> Dict[str, Any]:
        return {"status": "not_implemented", "job_id": job_id}


class GrokAudio:
    """
    xAI Grok Text-to-Speech (TTS) API.
    Uses the /v1/audio/speech endpoint — OpenAI-compatible.
    Default voice: Eve (energetic, upbeat).
    Available voices: ara, eve, rex, sal, leo
    """

    VOICES = ["ara", "eve", "rex", "sal", "leo"]
    DEFAULT_VOICE = "eve"

    def __init__(self, model: str = "grok-tts-aurora"):
        self.model = model

    def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        response_format: str = "mp3",
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Eve (or any xAI voice).

        Returns:
            {"audio_bytes": bytes, "format": str} on success
            {"error": str} on failure
        """
        client = _get_client()
        voice = voice.lower()
        if voice not in self.VOICES:
            voice = self.DEFAULT_VOICE
        try:
            response = client.audio.speech.create(
                model=self.model,
                input=text,
                voice=voice,
                response_format=response_format,
                speed=speed,
            )
            audio_data = response.content
            return {
                "audio_bytes": audio_data,
                "format": response_format,
                "voice": voice,
                "model": self.model,
                "text_length": len(text),
            }
        except Exception as e:
            return {"error": str(e), "model": self.model}


class GrokVoiceAgent:
    """
    xAI Grok Real-Time Voice Agent API.
    WebSocket speech-to-speech — OpenAI Realtime compatible.
    Endpoint: wss://api.x.ai/v1/realtime
    Default voice: Eve. Pricing: $0.05/minute.
    """

    REALTIME_URL = "wss://api.x.ai/v1/realtime"
    DEFAULT_VOICE = "Eve"

    def get_session_config(
        self,
        voice: str = DEFAULT_VOICE,
        system_prompt: str = "You are Mimi, a helpful AI assistant.",
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        config: Dict[str, Any] = {
            "model": "grok-2",
            "voice": voice,
            "instructions": system_prompt,
            "modalities": ["audio", "text"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500,
            },
        }
        if tools:
            config["tools"] = tools
        return config

    def get_connection_headers(self) -> Dict[str, str]:
        key = os.getenv("XAI_API_KEY", "")
        return {
            "Authorization": f"Bearer {key}",
            "OpenAI-Beta": "realtime=v1",
        }
