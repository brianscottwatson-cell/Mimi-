"""
Primary orchestrator agent that routes requests to specialized agents.
"""
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from agents.specialized_agents import SpecializedAgentFactory


class PrimaryAgent:
    """
    Primary orchestrator agent that:
    1. Understands user requests
    2. Decides which specialized agent(s) to use
    3. Coordinates between multiple agents if needed
    4. Synthesizes final responses
    """

    def __init__(self, model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize the primary agent.

        Args:
            model_provider: "anthropic" or "kimi"
            model_name: Specific model to use
        """
        self.model_provider = model_provider
        self.model_name = model_name

        # Create the primary reasoning agent
        self.agent = BaseAgent(
            name="Primary Orchestrator",
            role="Primary Agent & Task Router",
            system_prompt=self._get_system_prompt(),
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

        # Cache for specialized agents (create on demand)
        self.specialized_agents: Dict[str, BaseAgent] = {}

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the primary agent."""
        agent_types = SpecializedAgentFactory.get_all_agent_types()
        agent_list = "\n".join([f"- {key}: {desc}" for key, desc in agent_types.items()])

        return f"""You are the Primary Orchestrator Agent, a highly intelligent AI assistant that coordinates a team of specialized agents.

Your responsibilities:
1. Understand user requests and determine the best approach
2. Decide if you can handle the request directly or need to delegate to specialists
3. Route tasks to appropriate specialized agents
4. Coordinate between multiple agents when needed
5. Synthesize information from specialists into coherent responses
6. Provide direct assistance for general queries

Available Specialized Agents:
{agent_list}

When to delegate:
- Delegate to specialists when the task requires deep domain expertise
- For complex tasks, you may need to consult multiple specialists
- For general questions or simple tasks, handle them directly

How to delegate:
When you need a specialist, format your response as:
{{
    "action": "delegate",
    "agent": "agent_type",
    "task": "specific task for the specialist"
}}

Example:
User: "Help me research the best SEO practices for my e-commerce site"
Your response:
{{
    "action": "delegate",
    "agent": "seo",
    "task": "Research and provide best SEO practices for e-commerce websites, including on-page optimization, technical SEO, and content strategy"
}}

For direct responses, just respond normally without JSON formatting.

Be helpful, intelligent, and efficient in routing tasks to get the best results for users."""

    def _parse_delegation(self, response: str) -> Optional[Dict[str, str]]:
        """Parse if the primary agent wants to delegate to a specialist."""
        import json

        try:
            # Look for JSON in the response
            lines = response.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('{') and '"action"' in line and '"delegate"' in line:
                    try:
                        delegation = json.loads(line)
                        if delegation.get("action") == "delegate":
                            return delegation
                    except json.JSONDecodeError:
                        # Try multi-line JSON
                        json_str = '\n'.join(lines[i:])
                        try:
                            delegation = json.loads(json_str)
                            if delegation.get("action") == "delegate":
                                return delegation
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        return None

    def _get_or_create_specialist(self, agent_type: str) -> BaseAgent:
        """Get or create a specialized agent."""
        if agent_type not in self.specialized_agents:
            self.specialized_agents[agent_type] = SpecializedAgentFactory.create_agent(
                agent_type,
                model_provider=self.model_provider,
                model_name=self.model_name
            )
        return self.specialized_agents[agent_type]

    def chat(self, message: str) -> Dict[str, Any]:
        """
        Process a user message.

        Args:
            message: User's message

        Returns:
            Dict containing response and metadata
        """
        # Get initial response from primary agent
        primary_response = self.agent.chat(message)

        # Check if primary agent wants to delegate
        delegation = self._parse_delegation(primary_response)

        if delegation:
            agent_type = delegation.get("agent")
            task = delegation.get("task")

            if not agent_type or not task:
                return {
                    "response": "I wanted to delegate this task, but encountered an error in the delegation format.",
                    "agent_used": "primary",
                    "error": "Invalid delegation format"
                }

            try:
                # Get the specialist
                specialist = self._get_or_create_specialist(agent_type)

                # Have the specialist handle the task
                specialist_response = specialist.chat(task)

                # Have primary agent synthesize the specialist's response
                synthesis_prompt = f"""The {agent_type} specialist provided this response to the user's request:

---
{specialist_response}
---

Please synthesize this into a helpful response for the user. Add any additional context or suggestions if appropriate."""

                final_response = self.agent.chat(synthesis_prompt)

                return {
                    "response": final_response,
                    "agent_used": agent_type,
                    "specialist_response": specialist_response,
                    "delegated": True
                }

            except Exception as e:
                return {
                    "response": f"I attempted to delegate to the {agent_type} specialist, but encountered an error: {str(e)}",
                    "agent_used": "primary",
                    "error": str(e),
                    "delegated": False
                }
        else:
            # Primary agent handled it directly
            return {
                "response": primary_response,
                "agent_used": "primary",
                "delegated": False
            }

    def reset(self):
        """Reset all conversation history."""
        self.agent.reset_conversation()
        for specialist in self.specialized_agents.values():
            specialist.reset_conversation()

    def get_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            "primary_agent": self.agent.get_info(),
            "active_specialists": {
                agent_type: agent.get_info()
                for agent_type, agent in self.specialized_agents.items()
            },
            "available_specialists": list(SpecializedAgentFactory.get_all_agent_types().keys())
        }

    def switch_model(self, model_provider: str, model_name: str):
        """
        Switch the model provider/name for all agents.

        Args:
            model_provider: New model provider
            model_name: New model name
        """
        self.model_provider = model_provider
        self.model_name = model_name

        # Reset and recreate primary agent with new model
        self.agent = BaseAgent(
            name="Primary Orchestrator",
            role="Primary Agent & Task Router",
            system_prompt=self._get_system_prompt(),
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

        # Clear specialist cache (they'll be recreated with new model on demand)
        self.specialized_agents = {}
