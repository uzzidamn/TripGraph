# TripGraph AI

# Travel Intent Extraction Service
Version:1.0

---
# 1.Overview

## Purpose
This layer provides travel intent extraction capabilities for TripGraph AI.

The system processes natural language travel conversations and generates structured travel constraints that can be consumed by downstream planning systems and knowledge graph systems.

The output of this level generates a structured travel intent based on user requirements.
---

# 2. Architecture Pattern

Follow Augemented LLM Architecture

Travel Conversation -> Prompt Builder -> LLM 
-> Structured Travel Intent

# 3.Capabilities

This layer supports:

- Travel conversation understanding
- Budget extraction
- Duration extraction
- Origin extraction
- Activity extraction
- Travel preference extraction
- Restriction and avoidance extraction
- Structured JSON generation

---

## Expected Outcome

Given a travel conversation:

Aman: Budget under 15k

Rahul: Need rafting

Teja: Weekend trip

The system should generate:

{
  "budget": 15000,
  "activities": ["rafting"],
  "duration": "weekend"
}

The extracted travel intent should preserve all user-provided constraints and present them in a structured format suitable for downstream processing.

# Functional Requirements

The system shall:

- Extract budget constraints
- Extract trip duration constraints
- Extract Origin Locations
- Extract preferred activities
- Extract travel restrictions and avoidances
- Generate Valid JSON Output
- Preserve all extracted constraints in the final output

# 4. Configuration Management

## Configuration Sources

This service should load runtime configuration from:
1. Environment Variables

## Environment Variables
Location: .env
Example:

```
LLM_PROVIDER = google
LLM_MODEL = gemini-2.0-flash
LLM_Temperature = 0.0
LLM_MAX_TOKENS = 2048

```
# 5. Prompt Requirements

The prompt shall instruct the model to:
- Extract Travel Constraints
- Return Valid JSON Only
- Avoid Generating Recommendations
- Avoid Generating Explanations
- Avoid Making assumptions
- Preserve all user-provided constraints

# 6.Output Formt

``` Example Output:

{
  "budget": 15000,
  "duration": "weekend",
  "origin": "Bangalore",
  "destination": "Coorg",
  "activities": [
    "rafting"
  ],
  "avoid": [
    "flights"
  ]
}
```
# 7. Deliverables
- Configuration Loader
- Prompt Builder
- LLM Client
- Travel Intent Extractor
- Output Schema Definition

# 7.Acceptance Criteria

## 1. Budget Extraction
Given a conversation containing a budget constraint,
The system shall extract the budget value and include it in the output JSON.

Example:
Input:
Budget under 15000

Output:
{
    "budget": 15000
}

## 2. Duration Extraction
Given a conversation containing trip duration information,
the system shall extract the duration and include it in the 
output JSON.

## 3. Origin Extraction

Given a conversation containing an origin location,
the system shall extract the origin location

## 4. Destiniation Extraction
Given a conversation containing a destination location,
The service shall extract the destination.

## 5. Activity Extraction
Given a converstation containing activity preference,
the system shall extract all mentioned activities.

## 6. Avoidance Extraction
Given a conversation containing restrictions,
the system shall extract all avoidances

## 7. Multiple Constraint Extraction
Given a conversation containing multiple constraint types,
the system shall extract all supported constraints in a single-response.

## 8. Valid JSON Output
The service should always return syntatically correct JSON

