from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.weather_alerts import (
    fetch_ontario_weather_alerts,
)


router = APIRouter(
    prefix="/alerts",
    tags=["official alerts"],
)


@router.get("")
async def get_alerts() -> dict[str, Any]:
    try:
        return await fetch_ontario_weather_alerts()
    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error