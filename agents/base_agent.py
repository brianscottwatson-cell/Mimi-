"""
Base agent class for all AI agents in the system.
"""
import json
import os
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
import openai
from agents.tools import AgentTools


class BaseAgent:
    """Base class for all AI agents."""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model_provider: str = "anthropic",
        model_name: str = "claude-sonnet-4-5-20250929",
        tools_enabled: bool = True,
        max_tokens: int = 4000
    ):
        """
        Initialize an agent.

        Args:
            name: Agent's name
            role: Agent's role/expertise
            system_prompt: System prompt defining agent's behavior
            model_provider: "anthropic" or "kimi" (or other providers)
            model_name: Specific model to use
            tools_enabled: Whether this agent can use tools
            max_tokens: Maximum tokens in response
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model_provider = model_provider
        self.model_name = model_name
        self.tools_enabled = tools_enabled
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, str]] = []
        self.tools = AgentTools()

        # Initialize API clients
        if model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = Anthropic(api_key=api_key)
        elif model_provider == "kimi":
            # Kimi K2 uses OpenAI-compatible API
            api_key = os.getenv("KIMI_API_KEY")
            if not api_key:
                raise ValueError("KIMI_API_KEY not found in environment")
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1"  # Kimi API endpoint
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        if not self.tools_enabled:
            return {"error": "Tools are not enabled for this agent"}

        tool_method = getattr(self.tools, tool_name, None)
        if not tool_method:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            result = tool_method(**parameters)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def _check_for_tool_use(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Check if the response contains a tool use request."""
        if not self.tools_enabled:
            return None

        # Look for JSON tool requests in the response
        try:
            # Try to find JSON blocks in the response
            lines = response_text.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('{') and '"tool"' in line:
                    # Try to parse as JSON
                    try:
                        tool_request = json.loads(line)
                        if "tool" in tool_request and "parameters" in tool_request:
                            return tool_request
                    except json.JSONDecodeError:
                        # Try multi-line JSON
                        json_str = '\n'.join(lines[i:])
                        try:
                            tool_request = json.loads(json_str)
                            if "tool" in tool_request and "parameters" in tool_request:
                                return tool_request
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        return None

    def chat(self, message: str, max_tool_iterations: int = 3) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User's message
            max_tool_iterations: Maximum number of tool use iterations

        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Tool use loop
        for iteration in range(max_tool_iterations):
            # Get response from model
            if self.model_provider == "anthropic":
                response = self._chat_anthropic()
            elif self.model_provider == "kimi":
                response = self._chat_kimi()
            else:
                response = "Error: Unsupported model provider"

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            # Check if agent wants to use a tool
            tool_request = self._check_for_tool_use(response)

            if tool_request:
                # Execute the tool
                tool_result = self._execute_tool(
                    tool_request["tool"],
                    tool_request["parameters"]
                )

                # Add tool result to conversation
                tool_message = f"Tool Result:\n{json.dumps(tool_result, indent=2)}"
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_message
                })

                # Continue the loop to get final response
            else:
                # No tool use, return the response
                return response

        # If we've exhausted iterations, return the last response
        return response

    def _chat_anthropic(self) -> str:
        """Get response from Anthropic's Claude."""
        try:
            # Build messages (exclude system message)
            messages = self.conversation_history.copy()

            # Add tool descriptions to system prompt if tools enabled
            system_prompt = self.system_prompt
            if self.tools_enabled:
                system_prompt += "\n\n" + self.tools.get_tool_descriptions()

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )

            # Extract text from response
            if hasattr(response, "content") and response.content:
                first = response.content[0]
                return getattr(first, "text", str(first))

            return str(response)
        except Exception as e:
            return f"Error communicating with Claude: {str(e)}"

    def _chat_kimi(self) -> str:
        """Get response from Kimi K2."""
        try:
            # Build messages with system message
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            # Add tool descriptions if tools enabled
            if self.tools_enabled:
                messages[0]["content"] += "\n\n" + self.tools.get_tool_descriptions()

            messages.extend(self.conversation_history)

            response = self.client.chat.completions.create(
                model=self.model_name if self.model_name.startswith("moonshot") else "moonshot-v1-8k",
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with Kimi: {str(e)}"

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "role": self.role,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "tools_enabled": self.tools_enabled,
            "conversation_length": len(self.conversation_history)
        }
