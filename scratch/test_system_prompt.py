import sys
import os
import httpx
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents_augmented.prompts import SYSTEM_PROMPT
from backend.agents_augmented.tool_registry import get_claude_tool_schemas

url = "http://localhost:11434/v1/chat/completions"

tools = []
for t in get_claude_tool_schemas():
    tools.append({
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"]
        }
    })

payload = {
    "model": "qwen2.5:3b",
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Plan a trip based on these group chat messages:\n\n"
                "- Guys let's plan a trip from Gurugram\n"
                "- Maybe Rishikesh? I want to do rafting\n"
                "- Budget around 5000 per person\n"
                "- Weekend trip, 4 of us\n\n"
                "Use the available tools."
            )
        }
    ],
    "tools": tools,
    "temperature": 0,
    "stream": False
}

try:
    response = httpx.post(url, json=payload, timeout=30.0)
    print("Status:", response.status_code)
    print("Response choice:", json.dumps(response.json()["choices"][0]["message"], indent=2))
except Exception as e:
    print("Error:", e)
