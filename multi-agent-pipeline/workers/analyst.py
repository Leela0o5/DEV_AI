import os
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """You are a data analysis specialist agent.

Your job is to analyze information, identify patterns, provide insights, and reason about problems.
Focus on logical reasoning, critical thinking, and actionable insights.

Return your response as JSON with this structure:
{
    "analysis": "Main analysis and findings",
    "insights": ["List of key insights discovered"],
    "patterns": ["Patterns or trends identified"],
    "recommendations": ["Actionable recommendations"],
    "reasoning": "Step-by-step reasoning process"
}
"""

def execute(task: str) -> Dict[str, Any]:
    """Execute analysis task and return structured results."""
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"Analysis task: {task}\n\nProvide your analysis in the specified JSON format.",
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )
    
    import json
    try:
        result = json.loads(response.text)
        result["worker"] = "analyst"
        result["task"] = task
        return result
    except json.JSONDecodeError:
        return {
            "worker": "analyst",
            "task": task,
            "analysis": response.text,
            "insights": [],
            "patterns": [],
            "recommendations": [],
            "reasoning": "",
            "raw_response": True
        }
