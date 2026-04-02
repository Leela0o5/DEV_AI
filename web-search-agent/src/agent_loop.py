from google import genai
from google.genai import types
from tool import TOOLS, SEARCH_TOOL


def run(client: genai.Client, query: str) -> tuple[str, int]:
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=query)])]
    tool_calls = 0

    while True:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="You are a helpful assistant. Use web_search when you need current or factual information.",
                tools=[SEARCH_TOOL],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        if not response.function_calls:
            return response.text.strip(), tool_calls

        # model wants to call one or more tools — execute them
        fn_call_content = response.candidates[0].content
        contents.append(fn_call_content)

        response_parts = []
        for fn_call in response.function_calls:
            result = TOOLS[fn_call.name](**fn_call.args)
            tool_calls += 1
            response_parts.append(
                types.Part.from_function_response(
                    name=fn_call.name,
                    response={"result": result},
                )
            )

        contents.append(types.Content(role="tool", parts=response_parts))
