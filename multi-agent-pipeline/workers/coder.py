import os
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """You are a code generation specialist agent.

Your job is to write clean, well-structured, production-quality code.
Follow best practices, include error handling, and make code readable.

Return your response as JSON with this structure:
{
    "code": "The generated code",
    "language": "Programming language used",
    "explanation": "Brief explanation of the code",
    "dependencies": ["List of required packages/imports"],
    "usage_example": "How to use the code"
}
"""

def execute(task: str) -> Dict[str, Any]:
    """Execute coding task and return structured results."""
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"Coding task: {task}\n\nProvide your code in the specified JSON format.",
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )
    
    import json
    try:
        result = json.loads(response.text)
        result["worker"] = "coder"
        result["task"] = task
        return result
    except json.JSONDecodeError:
        return {
            "worker": "coder",
            "task": task,
            "code": response.text,
            "language": "unknown",
            "explanation": "",
            "dependencies": [],
            "usage_example": "",
            "raw_response": True
        }
