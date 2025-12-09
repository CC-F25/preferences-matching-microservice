from __future__ import annotations

import os
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, status, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

from models.preferences import PreferenceCreate, PreferenceRead
from models.preferences_matching import PreferenceInput

# ---------------------------------------------------------------------------
# Config – base URLs for your existing microservices
# ---------------------------------------------------------------------------

USERS_BASE_URL = os.environ.get("USERS_BASE_URL", "http://users-service:8000")
PREFS_BASE_URL = os.environ.get("PREFS_BASE_URL", "http://preferences-service:8000")

# -----------------------------------------------------------------------------#
# FastAPI app
# -----------------------------------------------------------------------------#

app = FastAPI(
    title="User Preferences Composite API",
    description=(
        "Composite microservice that ties Users and Preferences together. "
        "Frontend calls this service to create preferences for a user."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",                     # Firebase local emulator
        "https://cloud-computing-ui.web.app",        # deployed Firebase site
        "https://cloud-computing-ui.firebaseapp.com" # alt Firebase domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helper to call other microservices
# ---------------------------------------------------------------------------

async def get_user_or_404(user_id: UUID) -> dict:
    """
    Calls Users microservice to ensure a user exists and return its JSON.
    """
    url = f"{USERS_BASE_URL}/users/{user_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found in Users service")
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Users service error ({resp.status_code}): {resp.text}",
        )

    return resp.json()

async def create_preferences_in_service(pref: PreferenceCreate) -> PreferenceRead:
    """
    Call the Preferences microservice to create a Preference record.
    """
    url = f"{PREFS_BASE_URL}/preferences"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, json=pref.model_dump(mode="json"))

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Preferences service error ({resp.status_code}): {resp.text}",
        )

    data = resp.json()
    return PreferenceRead.model_validate(data)

# ---------------------------------------------------------------------------
# Composite endpoint
# ---------------------------------------------------------------------------
@app.post("/users/{user_id}/preferences", response_model=PreferenceRead, status_code=status.HTTP_201_CREATED)
async def create_user_preferenes(
    user_id: UUID = Path(..., description="User ID whose preferences are being set"),
    body: PreferenceInput = ...,
):
    """
    Creates preferences for a given user:
    1. Verify user exists by calling Users microservice.
    2. Fill in the PreferenceCreate payload using user_id and body
    3. Call Preferences microservice to create/replace preferences
    4. Return the resulting PreferenceRead to the frontend
    """
    # Step 1: Verify user exists
    user = await get_user_or_404(user_id)

    # Step 2: Build PreferenceCreate payload
    pref_create = PreferenceCreate(
        user_id=user_id,
        max_budget=body.max_budget,
        min_size=body.min_size,
        location_area=body.location_area,
        rooms=body.rooms,
    )

    # Step 3: Call Preferences microservice
    created_pref = await create_preferences_in_service(pref_create)

    # Step 4: Return to frontend
    return created_pref

@app.get("/")
def root():
    return {
        "message": "User-Preferences Composite API. See /docs for OpenAPI UI.",
        "users_base": USERS_BASE_URL,
        "prefs_base": PREFS_BASE_URL,
    }
