import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment. Set it in .env file.")

NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001")
SLACK_MCP_URL = os.getenv("SLACK_MCP_URL", "http://localhost:3002")


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "project-updates")

TIMEZONE = os.getenv("TIMEZONE", "UTC")
MORNING_STANDUP_HOUR = int(os.getenv("MORNING_STANDUP_HOUR", "9"))
END_OF_DAY_REPORT_HOUR = int(os.getenv("END_OF_DAY_REPORT_HOUR", "17"))
TASK_MONITOR_INTERVAL_MINUTES = int(
    os.getenv("TASK_MONITOR_INTERVAL_MINUTES", "30")
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def validate_config() -> None:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required")
    if NOTION_MCP_URL == "http://localhost:3001":
        print(
            "NOTION_MCP_URL using default (localhost:3001). "
            "Make sure Notion MCP server is running."
        )
    if SLACK_MCP_URL == "http://localhost:3002":
        print(
            "SLACK_MCP_URL using default (localhost:3002). "
            "Make sure Slack MCP server is running."
        )


if __name__ == "__main__":
    validate_config()
    print(" Configuration loaded successfully")
    print(f"  Gemini API: {GEMINI_API_KEY[:20]}...")
    print(f"  Notion MCP: {NOTION_MCP_URL}")
    print(f"  Slack MCP: {SLACK_MCP_URL}")
