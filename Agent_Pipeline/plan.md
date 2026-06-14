# Travel Intent Extraction Service — Implementation Plan

Source: `spec.md` (Version 1.0)

---

## Architecture

The spec defines an **Augmented LLM Architecture**:

```
Travel Conversation → Prompt Builder → LLM → Structured Travel Intent
```

No branching, no loops, no multi-agent workflow. A single linear pass: build a prompt from the conversation, send it to the LLM, return structured JSON.

---

## Output Schema

Defined in spec Section 6:

```json
{
  "budget": 15000,
  "duration": "weekend",
  "origin": "Bangalore",
  "destination": "Coorg",
  "activities": ["rafting"],
  "avoid": ["flights"]
}
```

| Field | Type | Acceptance Criterion |
|-------|------|----------------------|
| `budget` | integer | AC 1 |
| `duration` | string | AC 2 |
| `origin` | string | AC 3 |
| `destination` | string | AC 4 |
| `activities` | list of strings | AC 5 |
| `avoid` | list of strings | AC 6 |

---

## Deliverables

Taken directly from spec Section 7:

| Deliverable | File |
|-------------|------|
| Configuration Loader | `config.py` |
| Prompt Builder | `prompt_builder.py` |
| LLM Client | `llm_client.py` |
| Travel Intent Extractor | `extractor.py` |
| Output Schema Definition | `schema.py` |
| Entry point / test runner | `run.py` |
| Dependencies | `requirements.txt` |
| Environment template | `.env.example` |

---

## Implementation

### `config.py` — Configuration Loader

Loads the four variables from `.env` (spec Section 4):

```python
import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "google")
LLM_MODEL      = os.getenv("LLM_MODEL", "gemini-2.0-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_Temperature", "0.0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
```

`.env.example` (spec Section 4):
```
LLM_PROVIDER = google
LLM_MODEL = gemini-2.0-flash
LLM_Temperature = 0.0
LLM_MAX_TOKENS = 2048
```

---

### `schema.py` — Output Schema Definition

Defines the expected output structure. Used to document and validate the JSON the extractor returns.

```python
from typing import Optional
from pydantic import BaseModel

class TravelIntent(BaseModel):
    budget:      Optional[int]       = None
    duration:    Optional[str]       = None
    origin:      Optional[str]       = None
    destination: Optional[str]       = None
    activities:  Optional[list[str]] = None
    avoid:       Optional[list[str]] = None
```

All fields are optional — the spec says only include what is explicitly mentioned in the conversation.

---

### `prompt_builder.py` — Prompt Builder

Constructs the extraction prompt. The spec (Section 5) requires the prompt to:

- Extract travel constraints
- Return valid JSON only
- Avoid generating recommendations
- Avoid generating explanations
- Avoid making assumptions
- Preserve all user-provided constraints

```python
SYSTEM_PROMPT = """
You are a travel constraint extractor.

Extract travel constraints from the conversation and return a single valid JSON object.

Supported fields (only include what is explicitly stated):
- budget (integer)
- duration (string)
- origin (string)
- destination (string)
- activities (list of strings)
- avoid (list of strings)

Rules:
- Return ONLY the JSON object. No explanations, no recommendations, no markdown.
- Do not assume or invent values not stated in the conversation.
- Omit any field not mentioned.
- Preserve every constraint the user stated.
"""

def build_prompt(conversation: list[str]) -> str:
    chat_text = "\n".join(conversation)
    return f"{SYSTEM_PROMPT}\n\nConversation:\n{chat_text}"
```

---

### `llm_client.py` — LLM Client

Calls the LLM with the built prompt and returns the raw text response.

```python
import google.generativeai as genai
from config import LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def call_llm(prompt: str) -> str:
    model = genai.GenerativeModel(LLM_MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS,
        ),
    )
    return response.text.strip()
```

---

### `extractor.py` — Travel Intent Extractor

Ties together the full architecture pipeline: `Conversation → Prompt Builder → LLM → Structured Travel Intent`.

```python
import json
import re
from prompt_builder import build_prompt
from llm_client import call_llm
from schema import TravelIntent

def extract_travel_intent(conversation: list[str]) -> TravelIntent:
    prompt   = build_prompt(conversation)
    raw      = call_llm(prompt)

    # Remove markdown fences if the LLM wraps output in ```json ... ```
    cleaned  = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    data     = json.loads(cleaned)   # raises JSONDecodeError if invalid — AC 8
    return TravelIntent(**data)
```

---

### `run.py` — Entry Point

Runs each acceptance criterion from the spec.

```python
import json
from extractor import extract_travel_intent

def run(label: str, conversation: list[str]):
    print(f"\n--- {label} ---")
    result = extract_travel_intent(conversation)
    print(json.dumps(result.model_dump(exclude_none=True), indent=2))

# AC 1 — Budget
run("AC1: Budget", ["Aman: Budget under 15000"])

# AC 2 — Duration
run("AC2: Duration", ["Teja: Weekend trip"])

# AC 3 — Origin
run("AC3: Origin", ["Teja: Trip from Gurugram"])

# AC 4 — Destination
run("AC4: Destination", ["Rahul: We are going to Coorg"])

# AC 5 — Activities
run("AC5: Activities", ["Rahul: Need rafting"])

# AC 6 — Avoidances
run("AC6: Avoidances", ["Priya: No flights please"])

# AC 7 — Multiple constraints (spec expected outcome example)
run("AC7: Multiple constraints", [
    "Aman: Budget under 15k",
    "Rahul: Need rafting",
    "Teja: Weekend trip",
])

# AC 8 — Valid JSON is verified implicitly: json.loads inside extractor raises on bad output
```

---

## File Layout

```
Agent_Pipeline/
├── config.py          # Configuration Loader
├── prompt_builder.py  # Prompt Builder
├── llm_client.py      # LLM Client
├── extractor.py       # Travel Intent Extractor
├── schema.py          # Output Schema Definition
├── run.py             # Entry point / test runner
├── requirements.txt
├── .env.example
├── spec.md
└── plan.md
```

---

## Acceptance Criteria Coverage

| AC | Statement | File |
|----|-----------|------|
| 1 | Budget extracted as integer | `prompt_builder.py` field definition + `schema.py` |
| 2 | Duration extracted as string | `prompt_builder.py` field definition + `schema.py` |
| 3 | Origin extracted | `prompt_builder.py` field definition + `schema.py` |
| 4 | Destination extracted | `prompt_builder.py` field definition + `schema.py` |
| 5 | All activities extracted into list | `prompt_builder.py` field definition + `schema.py` |
| 6 | All avoidances extracted into list | `prompt_builder.py` field definition + `schema.py` |
| 7 | All constraints extracted in single response | Single LLM call in `extractor.py` |
| 8 | Always returns syntactically correct JSON | `json.loads` in `extractor.py` raises on invalid output |

---

## Implementation Order

1. `requirements.txt` + `.env` — install `google-generativeai`, `pydantic`, `python-dotenv`
2. `config.py` — load the four env variables
3. `schema.py` — define `TravelIntent` model
4. `prompt_builder.py` — write extraction prompt satisfying Section 5 rules
5. `llm_client.py` — wire Gemini call with config values
6. `extractor.py` — connect all components in the architecture pipeline
7. `run.py` — verify each acceptance criterion one by one
