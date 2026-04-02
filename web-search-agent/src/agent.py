import os
import sys
from dotenv import load_dotenv
from google import genai
from agent_loop import run


def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Set GEMINI_API_KEY in your .env file.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("Web Search Agent (type 'exit' to quit)\n")

    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break

        answer, count = run(client, query)
        print(f"\nAgent: {answer}")
        print(f"[tool used {count} time(s)]\n")


if __name__ == "__main__":
    main()
