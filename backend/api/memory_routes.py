from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.memory.store import get_user_memory, update_user_memory

router = APIRouter(prefix="/api", tags=["Memory"])


class MemoryPatch(BaseModel):
    preferred_origins: list[str] | None = None
    preferred_destinations: list[str] | None = None
    budget_range: dict[str, int] | None = None
    preferred_hotel_tier: str | None = None
    activity_preferences: list[str] | None = None
    avoidances: list[str] | None = None
    travel_style: str | None = None
    past_trips: list[Any] | None = None


@router.get("/memory")
def get_memory(current_user: User = Depends(get_current_user)) -> dict:
    return get_user_memory(current_user.id)


@router.patch("/memory")
def patch_memory(
    body: MemoryPatch,
    current_user: User = Depends(get_current_user),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    update_user_memory(current_user.id, updates)
    return get_user_memory(current_user.id)
