#!/usr/bin/env python3
"""
Test script to verify the system is set up correctly.
"""
import sys
import os


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from agents import BaseAgent, PrimaryAgent, SpecializedAgentFactory, AgentTools
        print("  ✓ Agent modules imported successfully")

        import anthropic
        print("  ✓ Anthropic SDK imported successfully")

        import fastapi
        print("  ✓ FastAPI imported successfully")

        import uvicorn
        print("  ✓ Uvicorn imported successfully")

        from bs4 import BeautifulSoup
        print("  ✓ BeautifulSoup imported successfully")

        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_agent_factory():
    """Test the agent factory."""
    print("\nTesting agent factory...")
    try:
        from agents.specialized_agents import SpecializedAgentFactory

        agents = SpecializedAgentFactory.get_all_agent_types()
        print(f"  ✓ Found {len(agents)} specialized agent types:")
        for agent_type, desc in agents.items():
            print(f"    - {agent_type}: {desc[:50]}...")

        return True
    except Exception as e:
        print(f"  ✗ Agent factory error: {e}")
        return False


def test_tools():
    """Test the tools module."""
    print("\nTesting tools...")
    try:
        from agents.tools import AgentTools

        tools = AgentTools.list_available_tools()
        print(f"  ✓ Found {len(tools)} available tools:")
        for tool in tools:
            print(f"    - {tool}")

        return True
    except Exception as e:
        print(f"  ✗ Tools error: {e}")
        return False


def check_api_keys():
    """Check if API keys are configured."""
    print("\nChecking API keys...")
    has_anthropic = os.getenv("ANTHROPIC_API_KEY")
    has_kimi = os.getenv("KIMI_API_KEY")

    if has_anthropic:
        key_preview = has_anthropic[:10] + "..." + has_anthropic[-4:]
        print(f"  ✓ ANTHROPIC_API_KEY found: {key_preview}")
    else:
        print("  ✗ ANTHROPIC_API_KEY not found")

    if has_kimi:
        key_preview = has_kimi[:10] + "..." + has_kimi[-4:]
        print(f"  ✓ KIMI_API_KEY found: {key_preview}")
    else:
        print("  ℹ KIMI_API_KEY not found (optional)")

    if not has_anthropic and not has_kimi:
        print("\n  ⚠ WARNING: No API keys configured!")
        print("  Set at least one of:")
        print("    export ANTHROPIC_API_KEY='your-key'")
        print("    export KIMI_API_KEY='your-key'")
        return False

    return True


def test_file_structure():
    """Test that all required files exist."""
    print("\nChecking file structure...")
    required_files = [
        "main.py",
        "api_server.py",
        "terminal_interface.py",
        "requirements.txt",
        "Procfile",
        "start.sh",
        ".env.example",
        "README.md",
        "agents/__init__.py",
        "agents/base_agent.py",
        "agents/primary_agent.py",
        "agents/specialized_agents.py",
        "agents/tools.py"
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} MISSING")
            all_exist = False

    return all_exist


def main():
    """Run all tests."""
    print("=" * 60)
    print("Multi-Agent AI System - Setup Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Agent Factory", test_agent_factory()))
    results.append(("Tools", test_tools()))
    results.append(("File Structure", test_file_structure()))
    results.append(("API Keys", check_api_keys()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Set your ANTHROPIC_API_KEY (if not already set)")
        print("  2. Run 'python main.py terminal' for terminal interface")
        print("  3. Run 'python main.py web' for web interface")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
