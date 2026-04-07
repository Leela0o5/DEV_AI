import logging

from .agent import ProjectManagerAgent
from .mcp_client import McpClient
from .tools import (
    format_eod_report,
    format_standup_message,
    send_slack_notification,
)

logger = logging.getLogger(__name__)


async def morning_standup(agent: ProjectManagerAgent, mcp: McpClient) -> None:

    logger.info("Running morning standup task")

    try:
    
        goal = "Fetch all tasks due today and post a standup message to Slack with today's priorities and any blockers"
        result = await agent.run(goal)

        if result.get("success"):
            logger.info(" Morning standup completed successfully")
        else:
            logger.warning(f" Morning standup incomplete: {result.get('result')}")

    except Exception as e:
        logger.error(f" Error in morning standup: {e}")


async def task_monitor(agent: ProjectManagerAgent, mcp: McpClient) -> None:
    logger.info("Running task monitor")

    try:
        goal = "Check all tasks for 'blocked' or 'urgent' status. If any are found, post a notification to Slack about the blockers."
        result = await agent.run(goal)

        if result.get("success"):
            logger.info(" Task monitor completed")
            if "blocker" in result.get("result", "").lower():
                logger.warning("Blockers detected and notified to team")
        else:
            logger.warning(f"  Task monitor incomplete: {result.get('result')}")

    except Exception as e:
        logger.error(f" Error in task monitor: {e}")


async def end_of_day_report(agent: ProjectManagerAgent, mcp: McpClient) -> None:
    logger.info("Running end-of-day report task")

    try:

        goal = "Generate an end-of-day summary: count completed tasks, list high-priority in-progress items, and identify any risks for tomorrow. Post this as a structured report to Slack."
        result = await agent.run(goal)

        if result.get("success"):
            logger.info("End-of-day report completed successfully")
        else:
            logger.warning(f"  Report incomplete: {result.get('result')}")

    except Exception as e:
        logger.error(f" Error in end-of-day report: {e}")


async def test_mcp_connection(mcp: McpClient) -> None:
   
    logger.info("Testing MCP server connections...")

    try:
        tools = await mcp.discover_tools()
        logger.info(f" MCP connected. Found {len(tools)} tools:")
        for tool_name in sorted(tools.keys()):
            logger.info(f"  {tool_name}")
    except Exception as e:
        logger.error(f" MCP connection test failed: {e}")
