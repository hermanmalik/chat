#!/home/herman/HMD/proj/chat/.venv/bin/python

import openai
import os
import sys
import signal
import json
from openai import OpenAI
from datetime import datetime
import glob

# Configuration
MODEL = "gpt-4o-mini"
SAVE_DIR = os.path.expanduser("~/HMD/proj/chat")
DEFAULT_SAVE_FILE = os.path.join(SAVE_DIR, ".chatgpt_saved.json")

# Common model aliases
MODEL_ALIASES = {
    "mini": "gpt-4o-mini",
    "4o-mini": "gpt-4o-mini",
    "4o": "gpt-4o",
    "4": "gpt-4",
    "3.5": "gpt-3.5-turbo",
    "turbo": "gpt-3.5-turbo",
}

# ANSI color codes
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

# Global state
client = None
messages = [{"role": "system", "content": "You are a helpful assistant. Provide clear, concise answers. For technical questions, give practical explanations with examples when helpful. ALWAYS be precise and rigorous. You can assume the person you are speaking to has advanced mathematical background and moderate background in computer science."}]
total_tokens_used = 0

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\nExiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def initialize_client():
    """Initialize OpenAI client with error handling."""
    global client
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print(f"{Colors.RED}Error: OPENAI_API_KEY environment variable not set.{Colors.RESET}")
        print("Please set your API key: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"{Colors.RED}Error initializing OpenAI client: {e}{Colors.RESET}")
        sys.exit(1)

def chat(query):
    global total_tokens_used
    messages.append({"role": "user", "content": query})

    print(f"\n{Colors.GREEN}", end="", flush=True)
    full_reply = ""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content

        print(Colors.RESET)
        messages.append({"role": "assistant", "content": full_reply})

        # Get token usage for the conversation
        try:
            usage_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=1,
            )
            if hasattr(usage_response, 'usage') and usage_response.usage:
                tokens = usage_response.usage.total_tokens
                total_tokens_used = tokens
                print(f"{Colors.DIM}[Tokens: {tokens}]{Colors.RESET}\n")
        except:
            print()  # Just newline if token tracking fails

    except openai.APIConnectionError as e:
        print(f"{Colors.RESET}\n{Colors.RED}Error: Could not connect to OpenAI API. Check your internet connection.{Colors.RESET}")
        print(f"Details: {e}\n")
        messages.pop()  # Remove the user message since we failed
    except openai.RateLimitError as e:
        print(f"{Colors.RESET}\n{Colors.RED}Error: Rate limit exceeded. Please wait and try again.{Colors.RESET}")
        print(f"Details: {e}\n")
        messages.pop()
    except openai.APIError as e:
        print(f"{Colors.RESET}\n{Colors.RED}Error: OpenAI API error occurred.{Colors.RESET}")
        print(f"Details: {e}\n")
        messages.pop()
    except Exception as e:
        print(f"{Colors.RESET}\n{Colors.RED}Error: An unexpected error occurred.{Colors.RESET}")
        print(f"Details: {e}\n")
        messages.pop()

def save_history(filename=None):
    """Save conversation history to a file."""
    if filename:
        filepath = os.path.join(SAVE_DIR, f"{filename}.json")
    else:
        filepath = DEFAULT_SAVE_FILE

    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(messages, f, indent=2)
        print(f"{Colors.GREEN}Conversation saved to {filepath}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error saving conversation: {e}{Colors.RESET}")

def load_history(filename=None):
    """Load conversation history from a file."""
    global messages, total_tokens_used

    if filename:
        filepath = os.path.join(SAVE_DIR, f"{filename}.json")
    else:
        filepath = DEFAULT_SAVE_FILE

    try:
        with open(filepath, "r") as f:
            messages = json.load(f)
        total_tokens_used = 0
        print(f"{Colors.GREEN}Conversation loaded from {filepath}{Colors.RESET}")
        print(f"{Colors.CYAN}Loaded {len(messages) - 1} messages{Colors.RESET}\n")
    except FileNotFoundError:
        print(f"{Colors.RED}Error: File not found: {filepath}{Colors.RESET}")
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Invalid JSON in file: {filepath}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error loading conversation: {e}{Colors.RESET}")

def list_conversations():
    """List all saved conversations."""
    try:
        pattern = os.path.join(SAVE_DIR, "*.json")
        files = glob.glob(pattern)

        if not files:
            print(f"{Colors.YELLOW}No saved conversations found.{Colors.RESET}")
            return

        print(f"{Colors.CYAN}Saved conversations:{Colors.RESET}")
        for filepath in sorted(files):
            filename = os.path.basename(filepath)
            try:
                mtime = os.path.getmtime(filepath)
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                # Load file to count messages
                with open(filepath, "r") as f:
                    data = json.load(f)
                    msg_count = len(data) - 1  # Exclude system message

                if filename == ".chatgpt_saved.json":
                    print(f"  {Colors.BOLD}[default]{Colors.RESET} - {msg_count} messages - {mtime_str}")
                else:
                    name = filename.replace(".json", "")
                    print(f"  {Colors.BOLD}{name}{Colors.RESET} - {msg_count} messages - {mtime_str}")
            except:
                print(f"  {filename} (error reading file)")
    except Exception as e:
        print(f"{Colors.RED}Error listing conversations: {e}{Colors.RESET}")

def clear_conversation():
    """Clear the current conversation."""
    global messages, total_tokens_used
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    total_tokens_used = 0
    print(f"{Colors.GREEN}Conversation cleared.{Colors.RESET}\n")

def view_conversation():
    """Display the current conversation."""
    print(f"\n{Colors.CYAN}Current conversation:{Colors.RESET}")
    for i, msg in enumerate(messages):
        if msg["role"] == "system":
            print(f"{Colors.DIM}[System]: {msg['content']}{Colors.RESET}")
        elif msg["role"] == "user":
            print(f"{Colors.BLUE}[User]: {msg['content']}{Colors.RESET}")
        elif msg["role"] == "assistant":
            # Truncate long messages
            content = msg['content']
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"{Colors.GREEN}[Assistant]: {content}{Colors.RESET}")
    print(f"\n{Colors.DIM}Total messages: {len(messages) - 1}{Colors.RESET}\n")

def multiline_input():
    """Get multi-line input from user."""
    print(f"\n{Colors.YELLOW}=== Multi-line input mode ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Type your message below. Enter '###' on a new line when done.{Colors.RESET}\n")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "###":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)

def switch_model(model_name=None):
    """Switch to a different model or show current model."""
    global MODEL

    if not model_name:
        # Just show current model
        print(f"{Colors.CYAN}Current model: {Colors.BOLD}{MODEL}{Colors.RESET}")
        print(f"\n{Colors.DIM}Available models:{Colors.RESET}")
        print(f"  gpt-4o-mini (aliases: mini, 4o-mini)")
        print(f"  gpt-4o (aliases: 4o)")
        print(f"  gpt-4 (aliases: 4)")
        print(f"  gpt-3.5-turbo (aliases: 3.5, turbo)")
        print()
        return

    # Resolve alias or use as-is
    new_model = MODEL_ALIASES.get(model_name.lower(), model_name)

    MODEL = new_model
    print(f"{Colors.GREEN}Switched to model: {Colors.BOLD}{MODEL}{Colors.RESET}\n")

def print_help():
    """Display help information."""
    print(f"\n{Colors.CYAN}Available commands:{Colors.RESET}")
    print(f"  {Colors.BOLD}/exit, /quit{Colors.RESET}    - Exit the program")
    print(f"  {Colors.BOLD}/save [name]{Colors.RESET}    - Save conversation (optionally with a name)")
    print(f"  {Colors.BOLD}/load [name]{Colors.RESET}    - Load conversation (optionally specify name)")
    print(f"  {Colors.BOLD}/list{Colors.RESET}           - List all saved conversations")
    print(f"  {Colors.BOLD}/clear{Colors.RESET}          - Clear current conversation")
    print(f"  {Colors.BOLD}/view{Colors.RESET}           - View current conversation history")
    print(f"  {Colors.BOLD}/multi{Colors.RESET}          - Enter multi-line input mode")
    print(f"  {Colors.BOLD}/model [name]{Colors.RESET}   - Show/switch AI model (e.g., /model 4, /model mini)")
    print(f"  {Colors.BOLD}/help{Colors.RESET}           - Show this help message")
    print(f"\n{Colors.DIM}Note: Commands start with '/'. Everything else is sent to ChatGPT.{Colors.RESET}\n")

def main():
    # Initialize OpenAI client
    initialize_client()

    # Start with CLI input
    if len(sys.argv) > 1:
        initial_input = " ".join(sys.argv[1:])
        chat(initial_input)

    # Enter interactive loop
    print(f"{Colors.CYAN}ChatGPT CLI - Type '/help' for commands{Colors.RESET}\n")

    try:
        while True:
            try:
                user_input = input(f"{Colors.BLUE}> {Colors.RESET}").strip()
            except EOFError:
                print("\nEOF received. Exiting.")
                break

            if not user_input:
                continue

            # Check if it's a command (starts with /)
            if user_input.startswith("/"):
                # Parse command and arguments
                command_input = user_input[1:]  # Remove the /
                parts = command_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else None

                # Handle commands
                if command in {"exit", "quit"}:
                    print("Goodbye.")
                    break
                elif command == "save":
                    save_history(args)
                    continue
                elif command == "load":
                    load_history(args)
                    continue
                elif command == "list":
                    list_conversations()
                    continue
                elif command == "clear":
                    clear_conversation()
                    continue
                elif command == "view":
                    view_conversation()
                    continue
                elif command == "multi":
                    multi_input = multiline_input()
                    if multi_input.strip():
                        chat(multi_input)
                    continue
                elif command == "model":
                    switch_model(args)
                    continue
                elif command == "help":
                    print_help()
                    continue
                else:
                    print(f"{Colors.RED}Unknown command: /{command}{Colors.RESET}")
                    print(f"{Colors.DIM}Type '/help' for available commands{Colors.RESET}\n")
                    continue

            # Otherwise treat as chat input
            chat(user_input)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")

if __name__ == "__main__":
    main()

