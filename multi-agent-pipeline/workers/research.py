import os
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """You are a research specialist agent.

Your job is to find information, sources, documentation, and relevant context for questions.
Focus on accuracy, credibility, and comprehensive coverage.

Return your response as JSON with this structure:
{
    "findings": "Main research findings and insights",
    "sources": ["List of sources, references, or documentation consulted"],
    "key_points": ["Bullet point list of key takeaways"],
    "confidence": "high|medium|low"
}
"""

def execute(task: str) -> Dict[str, Any]:
    """Execute research task and return structured results."""
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"Research task: {task}\n\nProvide your research findings in the specified JSON format.",
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )
    
    import json
    try:
        result = json.loads(response.text)
        result["worker"] = "research"
        result["task"] = task
        return result
    except json.JSONDecodeError:
        return {
            "worker": "research",
            "task": task,
            "findings": response.text,
            "sources": [],
            "key_points": [],
            "confidence": "medium",
            "raw_response": True
        }
