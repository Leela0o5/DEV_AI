import asyncio
import logging
import sys

from src.agent import ProjectManagerAgent
from src.config import validate_config
from src.mcp_client import McpClient
from src.scheduler import ProjectScheduler
from src.tasks import test_mcp_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting MCP Project Manager...")
    try:
        validate_config()
    except ValueError as e:
        logger.error(f" Configuration error: {e}")
        sys.exit(1)

    mcp = McpClient()
    await test_mcp_connection(mcp)
    agent = ProjectManagerAgent(mcp)
    logger.info("Agent initialized")

  
    scheduler = ProjectScheduler(agent, mcp)
    scheduler.start()
    logger.info("\n Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(
            f"  {job['name']} - {job['trigger']} (Next: {job['next_run_time']})"
        )

    logger.info("\n Project Manager running. Press Ctrl+C to stop.\n")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n Received interrupt signal")
    finally:
        scheduler.shutdown()
        await mcp.close()
        logger.info(" Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
