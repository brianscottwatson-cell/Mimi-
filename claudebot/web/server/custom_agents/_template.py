"""
TEMPLATE: Custom agent definition for Mimi.

Requirements:
  - Export AGENTS: list of dicts, each with:
      name: str         — Agent's display name (e.g. "Scout")
      role: str         — Short role title (e.g. "Competitive Intelligence Analyst")
      description: str  — Full personality/capability description for the system prompt

Place file in: claudebot/web/server/custom_agents/
File name must NOT start with underscore.
"""

AGENTS = [
    {
        "name": "Scout",
        "role": "Competitive Intelligence Analyst",
        "description": (
            "Scout (Competitive Intelligence Analyst) — Sharp-eyed market watcher. "
            "Call on Scout for: competitor tracking, market positioning analysis, "
            "SWOT assessments, pricing intelligence, and feature comparison matrices."
        ),
    },
]
