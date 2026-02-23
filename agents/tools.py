"""
Tools available to agents for enhanced capabilities.
"""
import json
import subprocess
import requests
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class AgentTools:
    """Collection of tools that agents can use."""

    @staticmethod
    def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Simulate web search (in production, use a real search API like Tavily, Brave, or Google).
        For now, this is a placeholder that returns mock results.
        """
        return {
            "tool": "web_search",
            "query": query,
            "results": [
                {
                    "title": f"Search result {i+1} for: {query}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"This is a mock search result for '{query}'. In production, integrate a real search API."
                }
                for i in range(num_results)
            ],
            "note": "This is a mock implementation. Integrate Tavily, Brave Search, or Google Custom Search API for real results."
        }

    @staticmethod
    def fetch_webpage(url: str) -> Dict[str, Any]:
        """Fetch and extract text content from a webpage."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return {
                "tool": "fetch_webpage",
                "url": url,
                "success": True,
                "content": text[:5000],  # Limit to first 5000 chars
                "length": len(text)
            }
        except Exception as e:
            return {
                "tool": "fetch_webpage",
                "url": url,
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def execute_code(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Execute code safely (sandboxed). Currently only supports Python.
        WARNING: In production, use proper sandboxing (Docker, etc.)
        """
        if language != "python":
            return {
                "tool": "execute_code",
                "success": False,
                "error": f"Language '{language}' not supported. Only Python is supported."
            }

        try:
            # WARNING: This is NOT safe for production!
            # Use proper sandboxing (Docker, E2B, etc.) in real deployment
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=5
            )

            return {
                "tool": "execute_code",
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "tool": "execute_code",
                "success": False,
                "error": "Code execution timed out (5s limit)"
            }
        except Exception as e:
            return {
                "tool": "execute_code",
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def read_file(filepath: str) -> Dict[str, Any]:
        """Read content from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "tool": "read_file",
                "filepath": filepath,
                "success": True,
                "content": content,
                "length": len(content)
            }
        except Exception as e:
            return {
                "tool": "read_file",
                "filepath": filepath,
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def write_file(filepath: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "tool": "write_file",
                "filepath": filepath,
                "success": True,
                "bytes_written": len(content)
            }
        except Exception as e:
            return {
                "tool": "write_file",
                "filepath": filepath,
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def list_available_tools() -> List[str]:
        """Return a list of all available tools."""
        return [
            "web_search",
            "fetch_webpage",
            "execute_code",
            "read_file",
            "write_file"
        ]

    @staticmethod
    def get_tool_descriptions() -> str:
        """Return descriptions of all available tools for agent prompts."""
        return """
Available Tools:
1. web_search(query, num_results=5) - Search the web for information
2. fetch_webpage(url) - Fetch and extract text from a webpage
3. execute_code(code, language="python") - Execute Python code safely
4. read_file(filepath) - Read content from a file
5. write_file(filepath, content) - Write content to a file

To use a tool, format your response as JSON:
{
    "tool": "tool_name",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    }
}
"""
