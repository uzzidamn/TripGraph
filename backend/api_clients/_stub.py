"""Uniform result shape for pending-key API clients.

When an API key is missing, clients return a `stub_unavailable(...)` so the
planner can call them unconditionally without try/except. The moment a real
implementation lands, swap the function body and keep the same return shape.
"""
from typing import Any, TypedDict


class APIResult(TypedDict):
    available: bool       # True when the client returned usable data
    reason: str           # "OK" | "API_KEY_PENDING" | "ERROR:<msg>"
    provider: str         # e.g. "skyscanner", "agoda_deals", "tomtom_traffic"
    data: Any             # provider-specific payload, or None when unavailable


def stub_unavailable(provider: str, reason: str = "API_KEY_PENDING") -> APIResult:
    return {
        "available": False,
        "reason": reason,
        "provider": provider,
        "data": None,
    }


def ok(provider: str, data: Any) -> APIResult:
    return {
        "available": True,
        "reason": "OK",
        "provider": provider,
        "data": data,
    }


def error(provider: str, message: str) -> APIResult:
    return {
        "available": False,
        "reason": f"ERROR:{message}",
        "provider": provider,
        "data": None,
    }
