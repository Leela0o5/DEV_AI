import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def format_task_list(tasks: list[dict]) -> str:
    if not tasks:
        return "No tasks found."

    formatted = []
    for task in tasks:
        title = task.get("title", "Untitled")
        status = task.get("status", "unknown").upper()
        priority = task.get("priority", "medium").upper()
        status_emoji = {
            "TODO": "📋",
            "IN_PROGRESS": "🔄",
            "BLOCKED": "🚫",
            "DONE": "✅",
        }.get(status, "•")

        formatted.append(
            f"{status_emoji} *{title}* — {status} (Priority: {priority})"
        )

    return "\n".join(formatted)


def parse_agent_response(response_text: str) -> dict[str, Any]:
    
    if "{" in response_text and "}" in response_text:
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse JSON from response: {e}")

    return {"text": response_text, "raw_response": True}


def notify_blocker(task_id: str, task_title: str, reason: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "message": f" *Task Blocked*: {task_title}\n_Reason_: {reason}",
        "priority": "high",
    }


def format_standup_message(tasks: list[dict], blockers: list[dict]) -> str:
    message_parts = [" *Daily Standup*"]

    message_parts.append("\n*Today's Tasks:*")
    task_list = format_task_list(tasks)
    message_parts.append(task_list)

    if blockers:
        message_parts.append("\n*Blockers:*")
        for blocker in blockers:
            message_parts.append(f"  • {blocker.get('message', 'Unknown blocker')}")
    else:
        message_parts.append("\n No blockers today")

    return "".join(message_parts)


def format_eod_report(completed: list[dict], in_progress: list[dict]) -> str:
    message_parts = [" *End of Day Report*"]
    message_parts.append(f"\n *Completed Today*: {len(completed)} tasks")
    for task in completed[:5]: 
        title = task.get("title", "Untitled")
        message_parts.append(f"  • {title}")
    if len(completed) > 5:
        message_parts.append(f"  ... and {len(completed) - 5} more")

   
    message_parts.append(
        f"\n *In Progress*: {len(in_progress)} tasks"
    )
    for task in in_progress[:5]: 
        title = task.get("title", "Untitled")
        priority = task.get("priority", "medium")
        message_parts.append(f"   {title} ({priority} priority)")

    return "".join(message_parts)


async def send_slack_notification(
    message: str, webhook_url: str, channel: str = None
) -> bool:
    if not webhook_url:
        logger.warning("Slack webhook URL not configured")
        return False

    import httpx

    payload = {
        "text": message,
        "mrkdwn": True,
    }

    if channel:
        payload["channel"] = channel

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10.0)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
