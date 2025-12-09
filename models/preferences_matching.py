# request model from frontend
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

class PreferenceInput(BaseModel):
    """
    What the frontend sends when creating preferences for a user.
    Note: user_id comes from the PATH, not from this body.
    """
    max_budget: Optional[int] = Field(None, ge=0)
    min_size: Optional[int] = Field(None, ge=0)
    location_area: Optional[List[str]] = None
    rooms: Optional[int] = Field(None, ge=0)