#!/usr/bin/env python3
"""
Quick demo of the multi-agent system.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents import PrimaryAgent

def demo():
    """Run a quick demo."""
    print("=" * 60)
    print("Multi-Agent AI System - Demo")
    print("=" * 60)
    print()

    # Initialize the primary agent
    print("Initializing primary agent with Claude Sonnet 4.5...")
    try:
        agent = PrimaryAgent(
            model_provider="anthropic",
            model_name="claude-sonnet-4-5-20250929"
        )
        print("✓ Agent initialized successfully!\n")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure your ANTHROPIC_API_KEY is set correctly.")
        return

    # Demo 1: Simple question (primary agent handles directly)
    print("-" * 60)
    print("Demo 1: Simple Question (Primary Agent)")
    print("-" * 60)
    question = "What is your role and how do you work?"
    print(f"Question: {question}\n")

    try:
        result = agent.chat(question)
        print(f"Agent: {result['agent_used']}")
        print(f"Response:\n{result['response']}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Demo 2: Task requiring specialist
    print("-" * 60)
    print("Demo 2: Research Task (Delegated to Research Specialist)")
    print("-" * 60)
    question = "What are the top 3 trends in AI for 2026?"
    print(f"Question: {question}\n")

    try:
        result = agent.chat(question)
        print(f"Agent: {result['agent_used']}")
        print(f"Delegated: {result['delegated']}")
        print(f"Response:\n{result['response']}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Show status
    print("-" * 60)
    print("System Status")
    print("-" * 60)
    status = agent.get_status()
    print(f"Primary Agent: {status['primary_agent']['name']}")
    print(f"Model: {status['primary_agent']['model_provider']} - {status['primary_agent']['model_name']}")
    print(f"Conversation Length: {status['primary_agent']['conversation_length']} messages")

    if status['active_specialists']:
        print(f"\nActive Specialists:")
        for agent_type, info in status['active_specialists'].items():
            print(f"  - {agent_type}: {info['conversation_length']} messages")

    print(f"\nAvailable Specialists: {', '.join(status['available_specialists'])}")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTry the full system:")
    print("  Terminal: python main.py terminal")
    print("  Web UI:   python main.py web")
    print()


if __name__ == "__main__":
    demo()
