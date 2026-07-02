from __future__ import annotations

from fastapi import APIRouter, HTTPException

from hardware_profiles import (
    get_active_profile_id,
    get_profile,
    list_profiles,
    set_active_profile_id,
)
from schemas import HardwareProfileResponse, HardwareProfileSelectRequest

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/hardware-profiles", response_model=list[HardwareProfileResponse])
async def hardware_profiles_list():
    return list_profiles()


@router.get("/hardware-profile", response_model=HardwareProfileResponse)
async def hardware_profile_active():
    return get_profile().to_dict()


@router.put("/hardware-profile", response_model=HardwareProfileResponse)
async def hardware_profile_set(body: HardwareProfileSelectRequest):
    try:
        profile = set_active_profile_id(body.profile_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return profile.to_dict()


@router.get("/hardware-profile/active-id")
async def hardware_profile_active_id():
    return {"profile_id": get_active_profile_id()}
