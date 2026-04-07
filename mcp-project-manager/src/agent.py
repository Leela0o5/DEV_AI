import json
import logging
from typing import Any

from google import genai

from . import config
from .mcp_client import McpClient
from .tools import parse_agent_response

logger = logging.getLogger(__name__)


class ProjectManagerAgent:

    def __init__(self, mcp_client: McpClient):
        self.mcp_client = mcp_client
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"
        self.max_turns = 10

    async def run(self, goal: str) -> dict[str, Any]:
        logger.info(f"Starting agent run: {goal}")

      
        await self.mcp_client.discover_tools()

        system_prompt = self._build_system_prompt()
        messages = [
            {
                "role": "user",
                "content": f"Goal: {goal}\n\nPlease accomplish this task using the available tools.",
            }
        ]

        # Tool calling loop
        for turn in range(self.max_turns):
            logger.debug(f"Agent turn {turn + 1}/{self.max_turns}")

          
            response = await self._call_gemini(
                messages=messages,
                system_prompt=system_prompt,
            )

           
            if response.get("stop_reason") == "STOP" or not response.get(
                "tool_calls"
            ):
                final_response = response.get("text", "")
                logger.info(f"Agent completed: {final_response[:100]}...")
                return {
                    "success": True,
                    "result": final_response,
                    "turns": turn + 1,
                }

           
            tool_results = await self._execute_tools(response.get("tool_calls", []))

            messages.append({
                "role": "assistant",
                "content": response.get("text", ""),
            })

           
            for tool_result in tool_results:
                messages.append({
                    "role": "user",
                    "content": json.dumps(tool_result),
                })

        logger.warning("Agent reached max turns without completion")
        return {
            "success": False,
            "result": "Max turns reached",
            "turns": self.max_turns,
        }

    async def _call_gemini(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> dict[str, Any]:
        try:
            converted_messages = self._convert_messages_to_gemini(messages)

            response = self.client.models.generate_content(
                model=self.model,
                contents=converted_messages,
                system_instruction=system_prompt,
                tools=[
                    {
                        "function_declarations": self.mcp_client.get_tool_definitions_for_gemini()
                    }
                ],
                generation_config=genai.types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                ),
            )

            return self._parse_gemini_response(response)

        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return {"text": f"Error: {str(e)}", "tool_calls": [], "stop_reason": "ERROR"}

    async def _execute_tools(self, tool_calls: list[dict]) -> list[dict]:
        results = []

        for call in tool_calls:
            tool_name = call.get("name")
            params = call.get("parameters", {})

            logger.debug(f"Executing tool: {tool_name} with params: {params}")

          
            result = await self.mcp_client.call_tool(tool_name, params)

            results.append({
                "tool_name": tool_name,
                "result": result,
                "success": "error" not in result,
            })

        return results

    def _build_system_prompt(self) -> str:
        return """You are an autonomous project manager agent with access to task management and messaging tools.

Your responsibilities:
1. Monitor task status and identify blockers
2. Post daily standups to Slack with today's priorities
3. Generate end-of-day reports summarizing completions
4. Ensure team is notified of any blockers or urgent updates

When given a goal:
- Use available tools to gather current information
- Make decisions about what actions to take
- Post messages to Slack when appropriate
- Return a clear summary of what you accomplished

Be concise, focus on high-priority items, and ensure all messages are clear and actionable.
Always use the available tools rather than making up information."""

    def _convert_messages_to_gemini(self, messages: list[dict]) -> list[dict]:
        converted = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]
            if isinstance(content, str) and content.startswith("{"):
                try:
                    parsed = json.loads(content)
                    if "tool_name" in parsed:
        
                        content = f"Tool result from {parsed['tool_name']}: {json.dumps(parsed['result'])}"
                except json.JSONDecodeError:
                    pass

            converted.append({
                "role": role,
                "parts": [{"text": content}],
            })

        return converted

    def _parse_gemini_response(self, response: Any) -> dict[str, Any]:
        result = {
            "text": "",
            "tool_calls": [],
            "stop_reason": response.candidates[0].finish_reason if response.candidates else "UNKNOWN",
        }

        if not response.candidates or not response.candidates[0].content.parts:
            return result
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text"):
                result["text"] = part.text
            elif hasattr(part, "function_call"):
                call = {
                    "name": part.function_call.name,
                    "parameters": dict(part.function_call.args),
                }
                result["tool_calls"].append(call)

        return result
