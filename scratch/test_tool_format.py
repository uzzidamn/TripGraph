import httpx
import json

url = "http://localhost:11434/v1/chat/completions"
# Let's request the routes for Gurugram using the get_routes tool
payload = {
    "model": "qwen2.5:3b",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. Use tools if needed to answer the user's question."},
        {"role": "user", "content": "Find routes starting from Gurugram."}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_routes",
                "description": "Fetch available routes from an origin city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Departure city name (e.g. 'Gurugram')"
                        }
                    },
                    "required": ["origin"]
                }
            }
        }
    ],
    "temperature": 0,
    "stream": False
}

response = httpx.post(url, json=payload, timeout=20.0)
print("Status:", response.status_code)
print("Raw Response:", json.dumps(response.json(), indent=2))
