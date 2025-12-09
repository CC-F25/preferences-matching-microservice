from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Any, Dict, List

# ---------------------------------------------------------------------------
# Pydantic models for composite API
# ---------------------------------------------------------------------------

class PreferenceCreate(BaseModel):
    """
    Payload we send to the preferences microservice.
    Fields match the PreferenceCreate model in preferences.py.
    """
    user_id: UUID
    max_budget: Optional[int] = Field(
        None,
        description="Maximum monthly rent budget (max_budget).",
    )
    min_size: Optional[int] = Field(
        None,
        description="Minimum desired apartment size in square feet (min_size).",
    )
    location_area: Optional[List[str]] = Field(
        None,
        description="List of preferred neighborhoods/locations.",
    )
    rooms: Optional[int] = Field(
        None,
        description="Desired number of rooms (e.g., bedrooms).",
    )


class UserPreferencesCreateRequest(BaseModel):
    """
    Payload that the FRONTEND sends to THIS composite microservice.
    It includes the user_id plus preference inputs, using the same
    field names as the preferences service.
    """
    user_id: UUID
    max_budget: Optional[int] = None
    min_size: Optional[int] = None
    location_area: Optional[List[str]] = None
    rooms: Optional[int] = None


class CompositeUserPreferences(BaseModel):
    """What this composite microservice returns."""
    user: Dict[str, Any]
    preferences: Dict[str, Any]
    links: Dict[str, str]


class CompositeUserPreferencesList(BaseModel):
    """For GET /user-preferences/{user_id} (may return 0..N preferences)."""
    user: Dict[str, Any]
    preferences: List[Dict[str, Any]]
    links: Dict[str, str]