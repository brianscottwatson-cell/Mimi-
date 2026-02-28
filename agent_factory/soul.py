"""
Soul Document Manager
Parses and applies .soul documents to agent configurations.
Soul documents define agent personality, voice, values, and behavior.
"""
import re
from typing import Dict, Any, Optional


def parse_soul(content: str) -> Dict[str, Any]:
    """
    Parse a .soul document (YAML-like with markdown sections).
    Returns a structured dict with personality fields.
    """
    soul: Dict[str, Any] = {
        "raw": content,
        "name": None,
        "role": None,
        "archetype": None,
        "personality": [],
        "voice": [],
        "values": [],
        "system_prompt": None,
        "greeting": None,
        "catchphrases": [],
    }

    # Extract name / role / archetype from top YAML-like lines
    for line in content.splitlines()[:15]:
        line = line.strip()
        if line.startswith("name:"):
            soul["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("role:"):
            soul["role"] = line.split(":", 1)[1].strip()
        elif line.startswith("archetype:"):
            soul["archetype"] = line.split(":", 1)[1].strip()

    # Extract System Prompt section
    sp_match = re.search(
        r"## System Prompt.*?\n([\s\S]+?)(?=\n##|\Z)", content, re.IGNORECASE
    )
    if sp_match:
        soul["system_prompt"] = sp_match.group(1).strip()

    # Extract Personality section bullets
    pers_match = re.search(
        r"## Personality\n([\s\S]+?)(?=\n##|\Z)", content, re.IGNORECASE
    )
    if pers_match:
        soul["personality"] = _extract_bullets(pers_match.group(1))

    # Extract Voice section bullets
    voice_match = re.search(
        r"## Voice.*?\n([\s\S]+?)(?=\n##|\Z)", content, re.IGNORECASE
    )
    if voice_match:
        soul["voice"] = _extract_bullets(voice_match.group(1))

    # Extract Core Values section bullets
    values_match = re.search(
        r"## Core Values\n([\s\S]+?)(?=\n##|\Z)", content, re.IGNORECASE
    )
    if values_match:
        soul["values"] = _extract_bullets(values_match.group(1))

    # Extract Catchphrases section
    catch_match = re.search(
        r"## Catchphrases.*?\n([\s\S]+?)(?=\n##|\Z)", content, re.IGNORECASE
    )
    if catch_match:
        soul["catchphrases"] = _extract_bullets(catch_match.group(1))

    return soul


def _extract_bullets(text: str):
    """Extract bullet-point lines from a markdown section."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("-", "*", "•")):
            items.append(line.lstrip("-*• ").strip())
        elif line.startswith('"') and line.endswith('"'):
            items.append(line.strip('"'))
    return items


def build_system_prompt_from_soul(soul: Dict[str, Any], base_prompt: str = "") -> str:
    """
    Compose a final system prompt from a parsed soul document,
    optionally prepending a base prompt.
    """
    parts = []

    if base_prompt:
        parts.append(base_prompt.strip())

    if soul.get("system_prompt"):
        parts.append(soul["system_prompt"])
    else:
        # Auto-build from fields
        if soul.get("name"):
            parts.append(f"You are {soul['name']}.")
        if soul.get("role"):
            parts.append(f"Your role: {soul['role']}.")
        if soul.get("archetype"):
            parts.append(f"Archetype: {soul['archetype']}.")
        if soul.get("personality"):
            parts.append("Personality traits:\n" + "\n".join(f"- {p}" for p in soul["personality"]))
        if soul.get("voice"):
            parts.append("Communication style:\n" + "\n".join(f"- {v}" for v in soul["voice"]))
        if soul.get("values"):
            parts.append("Core values:\n" + "\n".join(f"- {v}" for v in soul["values"]))
        if soul.get("catchphrases"):
            parts.append("Signature phrases: " + " | ".join(soul["catchphrases"]))

    return "\n\n".join(parts)


def validate_soul(content: str) -> Dict[str, Any]:
    """Validate a soul document and return parse results + any warnings."""
    parsed = parse_soul(content)
    warnings = []

    if not parsed.get("name"):
        warnings.append("No 'name:' field found in soul document")
    if not parsed.get("system_prompt") and not parsed.get("personality"):
        warnings.append("Soul document has no System Prompt or Personality section")

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "parsed": parsed,
    }
