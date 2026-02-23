"""
Terminal interface for the multi-agent system.
Allows local interaction via command line.
"""
import os
import sys
from agents import PrimaryAgent

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"


def print_banner():
    """Print welcome banner."""
    banner = f"""
{BOLD}{CYAN}╔════════════════════════════════════════════════════════╗
║           Multi-Agent AI System - Terminal            ║
║                                                        ║
║  Primary Agent + Specialized Sub-Agents               ║
╚════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)
    print(f"{YELLOW}Available commands:{RESET}")
    print(f"  {CYAN}help{RESET}      - Show available commands")
    print(f"  {CYAN}agents{RESET}    - List available specialized agents")
    print(f"  {CYAN}status{RESET}    - Show agent status")
    print(f"  {CYAN}reset{RESET}     - Reset conversation history")
    print(f"  {CYAN}model{RESET}     - Switch AI model")
    print(f"  {CYAN}quit/exit{RESET} - Exit the program")
    print()


def print_help():
    """Print help information."""
    print(f"\n{BOLD}{CYAN}Available Commands:{RESET}")
    print(f"  {CYAN}help{RESET}      - Show this help message")
    print(f"  {CYAN}agents{RESET}    - List all available specialized agents")
    print(f"  {CYAN}status{RESET}    - Show current agent status and model info")
    print(f"  {CYAN}reset{RESET}     - Clear conversation history")
    print(f"  {CYAN}model{RESET}     - Switch between AI models (Claude/Kimi)")
    print(f"  {CYAN}quit/exit{RESET} - Exit the program")
    print(f"\n{BOLD}How it works:{RESET}")
    print(f"  - Ask any question or give any task")
    print(f"  - The primary agent will handle it directly or delegate to specialists")
    print(f"  - Specialists: research, marketing, seo, digital_marketing,")
    print(f"    project_management, web_development")
    print()


def show_agents():
    """Show available specialized agents."""
    from agents.specialized_agents import SpecializedAgentFactory

    agents = SpecializedAgentFactory.get_all_agent_types()

    print(f"\n{BOLD}{CYAN}Available Specialized Agents:{RESET}\n")
    for agent_type, description in agents.items():
        print(f"  {MAGENTA}●{RESET} {BOLD}{agent_type}{RESET}")
        print(f"    {description}")
    print()


def show_status(primary_agent: PrimaryAgent):
    """Show agent status."""
    status = primary_agent.get_status()

    print(f"\n{BOLD}{CYAN}System Status:{RESET}\n")
    print(f"  {BOLD}Model Provider:{RESET} {status['primary_agent']['model_provider']}")
    print(f"  {BOLD}Model Name:{RESET} {status['primary_agent']['model_name']}")
    print(f"  {BOLD}Primary Agent:{RESET} {status['primary_agent']['name']}")
    print(f"  {BOLD}Conversation Length:{RESET} {status['primary_agent']['conversation_length']} messages")

    if status['active_specialists']:
        print(f"\n  {BOLD}Active Specialists:{RESET}")
        for agent_type, info in status['active_specialists'].items():
            print(f"    {MAGENTA}●{RESET} {agent_type}: {info['conversation_length']} messages")
    else:
        print(f"\n  {BOLD}Active Specialists:{RESET} None (will be created on demand)")

    print()


def switch_model(primary_agent: PrimaryAgent):
    """Switch AI model."""
    print(f"\n{BOLD}{CYAN}Switch AI Model:{RESET}\n")
    print(f"  1. Claude Sonnet 4.5 (Anthropic) - Most capable")
    print(f"  2. Kimi K2 (Moonshot) - Cost-effective alternative")
    print()

    choice = input(f"{CYAN}Choose (1 or 2):{RESET} ").strip()

    if choice == "1":
        primary_agent.switch_model("anthropic", "claude-sonnet-4-5-20250929")
        print(f"{GREEN}✓ Switched to Claude Sonnet 4.5{RESET}\n")
    elif choice == "2":
        primary_agent.switch_model("kimi", "moonshot-v1-8k")
        print(f"{GREEN}✓ Switched to Kimi K2{RESET}\n")
    else:
        print(f"{RED}Invalid choice{RESET}\n")


def main():
    """Run the terminal interface."""
    # Check for API keys
    has_anthropic = os.getenv("ANTHROPIC_API_KEY")
    has_kimi = os.getenv("KIMI_API_KEY")

    if not has_anthropic and not has_kimi:
        print(f"{RED}ERROR: No API keys found!{RESET}")
        print("Set at least one of:")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export KIMI_API_KEY='your-key'")
        return

    # Choose default model based on available keys
    if has_anthropic:
        model_provider = "anthropic"
        model_name = "claude-sonnet-4-5-20250929"
    else:
        model_provider = "kimi"
        model_name = "moonshot-v1-8k"

    print_banner()

    # Initialize primary agent
    try:
        primary_agent = PrimaryAgent(
            model_provider=model_provider,
            model_name=model_name
        )
        print(f"{GREEN}✓ Primary agent initialized with {model_provider}{RESET}\n")
    except Exception as e:
        print(f"{RED}ERROR: Failed to initialize agent: {e}{RESET}")
        return

    # Main interaction loop
    try:
        while True:
            try:
                user_input = input(f"{BOLD}{CYAN}You:{RESET} ")
            except EOFError:
                print()
                break

            if not user_input.strip():
                continue

            cmd = user_input.strip().lower()

            # Handle commands
            if cmd in ("quit", "exit"):
                print(f"{YELLOW}Goodbye!{RESET}")
                break
            elif cmd == "help":
                print_help()
                continue
            elif cmd == "agents":
                show_agents()
                continue
            elif cmd == "status":
                show_status(primary_agent)
                continue
            elif cmd == "reset":
                primary_agent.reset()
                print(f"{GREEN}✓ Conversation history cleared{RESET}\n")
                continue
            elif cmd == "model":
                switch_model(primary_agent)
                continue

            # Process user message
            try:
                print(f"{YELLOW}Thinking...{RESET}")

                result = primary_agent.chat(user_input)

                # Clear the "Thinking..." line
                print(f"\033[F\033[K", end="")  # Move up and clear line

                # Show which agent responded
                agent_used = result['agent_used']
                if result['delegated']:
                    print(f"{MAGENTA}[{agent_used} specialist]{RESET}")
                else:
                    print(f"{MAGENTA}[primary agent]{RESET}")

                # Show response
                response = result['response']
                for line in response.split('\n'):
                    print(f"{GREEN}{line}{RESET}")

                print()  # Extra newline for spacing

            except KeyboardInterrupt:
                print(f"\n{YELLOW}Cancelled{RESET}\n")
                continue
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Goodbye!{RESET}")


if __name__ == "__main__":
    main()
/Users/brianwatson/anthropic-test/agents/openclaw/dashboard.html
