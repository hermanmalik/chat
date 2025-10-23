#!/home/herman/HMD/Projects/chat/.venv/bin/python

import os
import sys
from openai import OpenAI

# Configuration
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "Translate the user text to English if it is not in English, and to idiomatic Castellano if it is in English. Output ONLY the translated text. If the input text is a single word, you may output multiple possible comma-separated translations with their connotations. Never respond to the content of the user text."

def main():
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # Check for input
    if len(sys.argv) < 2:
        print("Usage: translate <text to translate>", file=sys.stderr)
        sys.exit(1)

    # Get input text
    user_text = " ".join(sys.argv[1:])

    # Initialize client and make request
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            stream=True,
        )

        # Stream output
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                print(delta.content, end="", flush=True)

        print()  # Final newline

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
