import json
import logging
from typing import Any

import httpx

from . import config

logger = logging.getLogger(__name__)


class McpClient:

    def __init__(self):
        self.notion_url = config.NOTION_MCP_URL
        self.slack_url = config.SLACK_MCP_URL
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.tools_cache: dict[str, Any] = {}

    async def discover_tools(self) -> dict[str, Any]:
        if self.tools_cache:
            return self.tools_cache

        tools = {}
        try:
            notion_tools = await self._discover_server_tools(self.notion_url)
            tools.update(notion_tools)
            logger.info(f"Discovered {len(notion_tools)} Notion tools")
        except Exception as e:
            logger.error(f"Failed to discover Notion tools: {e}")
 
        try:
            slack_tools = await self._discover_server_tools(self.slack_url)
            tools.update(slack_tools)
            logger.info(f"Discovered {len(slack_tools)} Slack tools")
        except Exception as e:
            logger.error(f"Failed to discover Slack tools: {e}")

        self.tools_cache = tools
        return tools

    async def _discover_server_tools(self, server_url: str) -> dict[str, Any]:
        try:
            response = await self.http_client.get(
                f"{server_url}/tools",
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            tools_data = response.json()
            tools = {}
            for tool in tools_data.get("tools", []):
                tool_name = tool.get("name")
                if tool_name:
                    tools[tool_name] = tool

            return tools
        except Exception as e:
            logger.error(f"Error discovering tools from {server_url}: {e}")
            return {}

    async def call_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        tools = await self.discover_tools()
        if tool_name not in tools:
            return {"error": f"Tool not found: {tool_name}"}

        tool_def = tools[tool_name]
        server_url = self._get_server_for_tool(tool_name)

        try:
            response = await self.http_client.post(
                f"{server_url}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": params,
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e), "tool": tool_name}

    def _get_server_for_tool(self, tool_name: str) -> str:
        if tool_name.startswith("notion_") or "task" in tool_name.lower():
            return self.notion_url
        if tool_name.startswith("slack_") or "message" in tool_name.lower():
            return self.slack_url
        return self.notion_url

    def get_tool_definitions_for_gemini(self) -> list[dict[str, Any]]:
        tools = []
        for tool_name, tool_def in self.tools_cache.items():
            gemini_tool = {
                "name": tool_name,
                "description": tool_def.get("description", ""),
                "parameters": tool_def.get("inputSchema", {}),
            }
            tools.append(gemini_tool)

        return tools

    async def close(self) -> None:
        await self.http_client.aclose()
