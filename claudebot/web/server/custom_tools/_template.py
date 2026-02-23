"""
TEMPLATE: Custom tool for Mimi.
Copy this pattern when creating a new tool module.

Requirements:
  - Export TOOLS: list of Claude tool JSON schemas
  - Export HANDLERS: dict mapping tool_name -> handler_function
  - Handlers receive keyword arguments matching the schema properties
  - Return a JSON-serializable dict from each handler

Place file in: claudebot/web/server/custom_tools/
File name must NOT start with underscore.
"""


def my_example_tool(query: str, max_results: int = 5) -> dict:
    """Example tool handler."""
    return {
        "status": "ok",
        "query": query,
        "results": [f"Result {i+1} for '{query}'" for i in range(max_results)],
    }


# --- Required exports ---

TOOLS = [
    {
        "name": "my_example_tool",
        "description": "An example custom tool. Replace with a real description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max results to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
]

HANDLERS = {
    "my_example_tool": my_example_tool,
}
