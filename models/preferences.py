# taken from preferences microservice
from __future__ import annotations

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Core Base Model
# -----------------------------------------------------------------------------

class PreferenceBase(BaseModel):
    """
    Defines the core fields for user housing preferences.
    Corresponds to the non-timestamp fields in the User_Preferences table
    and the fields in the PreferenceInput schema.
    """
    user_id: UUID = Field(
        ..., 
        description="Unique ID of the user associated with these preferences.",
        json_schema_extra={"example": "b01fbc13-12d2-4f4f-9c9b-7d00e233b3ae"},
    )
    max_budget: Optional[int] = Field(
        None, 
        ge=0, 
        description="Maximum monthly rent budget (max_budget).",
        json_schema_extra={"example": 4000},
    )
    min_size: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum desired apartment size in square feet (min_size).",
        json_schema_extra={"example": 900},
    )
    # Note: The database schema uses 'location_area' as a single string (VARCHAR),
    # but the openapi.yaml used 'neighborhood' as a list of strings.
    # We will use 'neighborhood' as a List[str] for a flexible API, 
    # but rename to 'location_area' to match the database column name, 
    # allowing for multiple preferred neighborhoods.
    location_area: Optional[List[str]] = Field(
        None, 
        description="List of preferred neighborhoods/locations.",
        json_schema_extra={"example": ["Williamsburg", "Bushwick"]},
    )
    
    # We'll use 'rooms' for num_bedrooms from the API spec, 
    # as the DB uses 'min_size' and 'max_budget' but is missing a specific room/bedroom count field.
    rooms: Optional[int] = Field(
        None,
        ge=0,
        description="Desired number of rooms (e.g., bedrooms).",
        json_schema_extra={"example": 2},
    )


# -----------------------------------------------------------------------------
# Input/Create/Update Models
# -----------------------------------------------------------------------------

class PreferenceCreate(PreferenceBase):
    """Payload for creating or entirely replacing a user's preferences."""
    # Inherits all fields from PreferenceBase.
    # We use this for the POST / endpoint (create/replace).
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "b01fbc13-12d2-4f4f-9c9b-7d00e233b3ae",
                "max_budget": 4000,
                "min_size": 900,
                "location_area": ["Williamsburg", "Bushwick"],
                "rooms": 2,
            }
        }
    }


class PreferenceUpdate(BaseModel):
    """
    Partial update payload. Only fields provided will be updated.
    The user_id is taken from the path, not the body.
    """
    max_budget: Optional[int] = Field(
        None, 
        ge=0, 
        description="Maximum monthly rent budget.",
        json_schema_extra={"example": 3500},
    )
    min_size: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum desired apartment size in square feet.",
        json_schema_extra={"example": 1000},
    )
    location_area: Optional[List[str]] = Field(
        None, 
        description="List of preferred neighborhoods/locations (replaces existing list).",
        json_schema_extra={"example": ["Greenpoint", "Long Island City"]},
    )
    rooms: Optional[int] = Field(
        None,
        ge=0,
        description="Desired number of rooms (e.g., bedrooms).",
        json_schema_extra={"example": 3},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "max_budget": 3500,
                    "location_area": ["Greenpoint"],
                },
                {
                    "rooms": 3,
                },
            ]
        }
    }

# -----------------------------------------------------------------------------
# Read Model (Response)
# -----------------------------------------------------------------------------

class PreferenceRead(PreferenceBase):
    """Full preference record returned to the client."""
    # The DB schema uses 'preference_id', which we'll map to 'id' for convention.
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent preference ID (server generated).",
        json_schema_extra={"example": "9d1f8bc4-a03a-4e2b-8a8f-2c3e1d4f5a6b"},
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-11-18T10:00:00Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-11-18T11:30:00Z"},
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "9d1f8bc4-a03a-4e2b-8a8f-2c3e1d4f5a6b",
                "user_id": "b01fbc13-12d2-4f4f-9c9b-7d00e233b3ae",
                "max_budget": 4000,
                "min_size": 900,
                "location_area": ["Williamsburg", "Bushwick"],
                "rooms": 2,
                "created_at": "2025-11-18T10:00:00Z",
                "updated_at": "2025-11-18T11:30:00Z",
            }
        },
    }