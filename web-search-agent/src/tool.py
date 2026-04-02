from ddgs import DDGS
from google.genai import types


def web_search(query: str) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))

    if not results:
        return "No results found."

    output = []
    for i, r in enumerate(results, 1):
        output.append(
            f"[{i}] {r.get('title', '')}\n"
            f"    {r.get('body', '')}\n"
            f"    {r.get('href', '')}"
        )
    return "\n\n".join(output)


search_function = types.FunctionDeclaration(
    name="web_search",
    description="Search the web for current information. Use when the question needs up-to-date facts, news, or anything you're not sure about.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            }
        },
        "required": ["query"],
    },
)

SEARCH_TOOL = types.Tool(function_declarations=[search_function])

TOOLS = {"web_search": web_search}
