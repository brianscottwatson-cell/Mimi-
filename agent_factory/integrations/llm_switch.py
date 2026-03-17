"""
LLM Router — unified interface for switching between LLM providers.
Supports: Anthropic Claude, xAI Grok, OpenAI GPT, Moonshot Kimi.
"""
import os
from typing import List, Dict, Any, Optional


PROVIDERS = {
    "anthropic": {
        "models": [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
        ],
        "default": "claude-sonnet-4-6",
        "env_key": "ANTHROPIC_API_KEY",
        "description": "Anthropic Claude — state-of-the-art reasoning and instruction following",
    },
    "xai": {
        "models": [
            "grok-2",
            "grok-2-vision-1212",
            "grok-3",
            "grok-3-mini",
        ],
        "default": "grok-2",
        "env_key": "XAI_API_KEY",
        "description": "xAI Grok — real-time web knowledge, multimodal reasoning",
    },
    "openai": {
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "o3-mini",
        ],
        "default": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "description": "OpenAI GPT — versatile, widely integrated LLMs",
    },
    "kimi": {
        "models": [
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
            "kimi-k2",
        ],
        "default": "kimi-k2",
        "env_key": "KIMI_API_KEY",
        "description": "Moonshot Kimi — cost-effective long-context model",
    },
}


class LLMRouter:
    """Routes LLM completions to the appropriate provider."""

    def complete(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Run a completion and return the response text."""
        provider = provider.lower()

        if provider == "anthropic":
            return self._anthropic(model, system_prompt, messages, max_tokens, temperature)
        elif provider == "xai":
            return self._xai(model, system_prompt, messages, max_tokens, temperature)
        elif provider in ("openai", "kimi"):
            return self._openai_compat(provider, model, system_prompt, messages, max_tokens, temperature)
        else:
            return f"[Error] Unsupported provider: {provider}"

    # ------------------------------------------------------------------ #
    #  Anthropic                                                           #
    # ------------------------------------------------------------------ #

    def _anthropic(self, model, system_prompt, messages, max_tokens, temperature):
        try:
            from anthropic import Anthropic
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                return "[Error] ANTHROPIC_API_KEY not set"
            client = Anthropic(api_key=key)
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            return f"[Anthropic Error] {e}"

    # ------------------------------------------------------------------ #
    #  xAI Grok (OpenAI-compatible endpoint)                              #
    # ------------------------------------------------------------------ #

    def _xai(self, model, system_prompt, messages, max_tokens, temperature):
        try:
            import openai
            key = os.getenv("XAI_API_KEY")
            if not key:
                return "[Error] XAI_API_KEY not set"
            client = openai.OpenAI(
                api_key=key,
                base_url="https://api.x.ai/v1",
            )
            msgs = [{"role": "system", "content": system_prompt}] + messages
            resp = client.chat.completions.create(
                model=model,
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[xAI Error] {e}"

    # ------------------------------------------------------------------ #
    #  OpenAI-compatible (OpenAI, Kimi)                                   #
    # ------------------------------------------------------------------ #

    def _openai_compat(self, provider, model, system_prompt, messages, max_tokens, temperature):
        try:
            import openai
            cfg = PROVIDERS[provider]
            key = os.getenv(cfg["env_key"])
            if not key:
                return f"[Error] {cfg['env_key']} not set"

            base_url = None
            if provider == "kimi":
                base_url = "https://api.moonshot.cn/v1"

            client = openai.OpenAI(api_key=key, base_url=base_url)
            msgs = [{"role": "system", "content": system_prompt}] + messages
            resp = client.chat.completions.create(
                model=model,
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[{provider} Error] {e}"

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def is_supported(self, provider: str) -> bool:
        return provider.lower() in PROVIDERS

    def list_providers(self) -> Dict[str, Any]:
        result = {}
        for name, cfg in PROVIDERS.items():
            result[name] = {
                "models": cfg["models"],
                "default_model": cfg["default"],
                "description": cfg["description"],
                "configured": bool(os.getenv(cfg["env_key"])),
            }
        return result
