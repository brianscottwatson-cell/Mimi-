import os
import sys
import time
import anthropic

# ANSI colors (works in most modern terminals)
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def _extract_reply(response):
    if hasattr(response, "content") and response.content:
        first = response.content[0]
        # support attribute-style and dict-style
        try:
            return getattr(first, "text", None) or first.get("text")
        except Exception:
            return str(first)
    return str(response)


def welcome():
    banner = f"{BOLD}{CYAN}╔════════════════════════════════╗\n" \
             f"║   Claude 3 Haiku — Terminal   ║\n" \
             f"╚════════════════════════════════>{RESET}"
    print()
    print(f"{BOLD}{CYAN}Welcome to Claude 3 Haiku Chat — ask me anything!{RESET}")
    print(f"{YELLOW}Type 'quit' or 'exit' to leave. Press Ctrl-C to cancel.{RESET}")
    print()


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"{RED}ERROR: ANTHROPIC_API_KEY not found!{RESET}")
        print("Set it with: export ANTHROPIC_API_KEY='sk-...'")
        return

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-3-haiku-20240307"

    conversation = [
        {"role": "system", "content": "You are Claude, a helpful assistant."}
    ]

    welcome()

    try:
        while True:
            try:
                user_input = input(f"{BOLD}{CYAN}You: {RESET}")
            except EOFError:
                print()
                break

            if not user_input:
                continue

            cmd = user_input.strip().lower()
            if cmd in ("quit", "exit"):
                print(f"{YELLOW}Exiting chat. Goodbye!{RESET}")
                break

            # show the user's line (colored)
            print(f"{CYAN}You: {RESET}{user_input}")
            conversation.append({"role": "user", "content": user_input})

            try:
                response = client.messages.create(
                    model=model,
                    messages=conversation,
                    max_tokens=500,
                )

                reply = _extract_reply(response) or ""

                # print Claude's reply in green
                for line in str(reply).splitlines():
                    print(f"{GREEN}Claude: {RESET}{line}")

                conversation.append({"role": "assistant", "content": reply})

            except anthropic.APIError as e:
                print(f"{RED}API Error: {getattr(e, 'status_code', '?')} - {getattr(e, 'message', e)}{RESET}")
            except Exception as e:
                print(f"{RED}Other error: {e}{RESET}")

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Exiting chat.{RESET}")


if __name__ == "__main__":
    main()