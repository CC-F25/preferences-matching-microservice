from __future__ import annotations

import os
from uuid import UUID
from typing import Optional, Any, Dict, List

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.preferences_matching import PreferenceCreate, UserPreferencesCreateRequest, CompositeUserPreferences, CompositeUserPreferencesList

# ---------------------------------------------------------------------------
# Config: where are the other microservices?
# ---------------------------------------------------------------------------

USERS_SERVICE_BASE_URL = os.environ.get(
    "USERS_SERVICE_BASE_URL",
    "https://users-microservice-258517926293.us-central1.run.app",
)

PREFERENCES_SERVICE_BASE_URL = os.environ.get(
    "PREFERENCES_SERVICE_BASE_URL",
    "http://localhost:8000",  # preferences microservice running on same VM
)

PORT = int(os.environ.get("FASTAPIPORT", "8002"))  # composite service port

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Preferences Matching Composite Microservice",
    description=(
        "Composite microservice that links Users (Cloud Run) and "
        "Preferences (VM) via business logic."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",                     # Firebase local emulator
        "https://cloud-computing-ui.web.app",        # deployed front-end
        "https://cloud-computing-ui.firebaseapp.com" # alt Firebase domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper functions to talk to other microservices
# ---------------------------------------------------------------------------

async def create_preferences(pref_payload: PreferenceCreate) -> Dict[str, Any]:
    """POST to preferences microservice to create/update a preference record."""
    # Preferences main.py exposes POST "/" as the create/update
    url = f"{PREFERENCES_SERVICE_BASE_URL}/"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, json=pref_payload.model_dump())

    if resp.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        raise HTTPException(
            status_code=502,
            detail=f"Preferences microservice error on create: {resp.status_code} {resp.text}",
        )
    return resp.json()


async def fetch_preferences_for_user(user_id: UUID) -> list[Dict[str, Any]]:
    """
    GET preferences for a specific user by calling GET /{userId}
    on the preferences microservice.
    """
    url = f"{PREFERENCES_SERVICE_BASE_URL}/{user_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)

    if resp.status_code == status.HTTP_404_NOT_FOUND:
        # No preferences for this user
        return []
    if resp.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=502,
            detail=f"Preferences microservice error on get: {resp.status_code} {resp.text}",
        )

    data = resp.json()
    # preferences service returns a single object, so wrap into a list
    return [data]

async def fetch_user(user_id: UUID) -> Dict[str, Any]:
    """GET user from Users microservice, or raise 404/502."""
    url = f"{USERS_SERVICE_BASE_URL}/users/{user_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=404, detail="User not found in Users microservice")
    if resp.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=502,
            detail=f"Users microservice error: {resp.status_code} {resp.text}",
        )
    return resp.json()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Preferences Matching Composite Microservice",
        "links": {
            "create_user_preferences": "/user-preferences",
            "get_user_preferences": "/user-preferences/{user_id}",
        },
    }


@app.post(
    "/user-preferences",
    response_model=CompositeUserPreferences,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_preferences(payload: UserPreferencesCreateRequest):
    """
    Composite endpoint called by the FRONTEND.

    Flow:
    1. Validate that the user exists in Users microservice.
    2. Build a preferences payload (adding user_id).
    3. Create preferences via Preferences microservice.
    4. Return combined user + preferences + hypermedia links.
    """
    # 1. Ensure the user exists
    user = await fetch_user(payload.user_id)

    # 2. Build PreferenceCreate payload (field names aligned with preferences.py)
    pref_payload = PreferenceCreate(
        user_id=payload.user_id,
        max_budget=payload.max_budget,
        min_size=payload.min_size,
        location_area=payload.location_area,
        rooms=payload.rooms,
    )

    # 3. Create preferences in the preferences microservice
    pref = await create_preferences(pref_payload)

    # 4. Build hypermedia links (linked data + relative paths)
    links = {
        "self": f"/user-preferences/{payload.user_id}",
        "user": f"{USERS_SERVICE_BASE_URL}/users/{payload.user_id}",
        # direct link to the preferences resource for this user
        "preferences": f"{PREFERENCES_SERVICE_BASE_URL}/{payload.user_id}",
    }

    return CompositeUserPreferences(
        user=user,
        preferences=pref,
        links=links,
    )


@app.get(
    "/user-preferences/{user_id}",
    response_model=CompositeUserPreferencesList,
)
async def get_user_preferences(user_id: UUID):
    """
    Read composite view:
    - fetch user from Users
    - fetch preferences from Preferences (by user_id)
    """
    user = await fetch_user(user_id)
    prefs = await fetch_preferences_for_user(user_id)

    links = {
        "self": f"/user-preferences/{user_id}",
        "user": f"{USERS_SERVICE_BASE_URL}/users/{user_id}",
        "preferences": f"{PREFERENCES_SERVICE_BASE_URL}/{user_id}",
    }

    return CompositeUserPreferencesList(
        user=user,
        preferences=prefs,
        links=links,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
