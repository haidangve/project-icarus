import asyncio

import httpx
from fastapi import APIRouter, HTTPException, status

from app.schemas.fire import FireFeatureCollection
from app.services.fire_sources.cwfif import (
    CWFIFSourceError,
    fetch_current_ontario_fires,
)
from app.services.fire_sources.lio import (
    LIOSourceError,
    fetch_in_year_fire_perimeters,
)
from app.services.fire_sources.reconcile import (
    reconcile_fire_sources,
)


router = APIRouter(
    prefix="/fires",
    tags=["fires"],
)


@router.get(
    "",
    response_model=FireFeatureCollection,
    summary="Get current Ontario fires",
    description=(
        "Returns current agency-reported Ontario fires from CWFIF, "
        "enriched with exact-match LIO perimeter geometry when available."
    ),
)
async def get_fires() -> FireFeatureCollection:
    """
    Fetch and reconcile the current Ontario fire sources.

    CWFIF determines which incidents are active. LIO supplies perimeter
    geometry only after an exact agency-fire-ID match.
    """

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        try:
            cwfif_payload, lio_payload = await asyncio.gather(
                fetch_current_ontario_fires(client),
                fetch_in_year_fire_perimeters(client),
            )

        except (CWFIFSourceError, LIOSourceError) as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "fire_source_unavailable",
                    "message": str(error),
                },
            ) from error

    try:
        return reconcile_fire_sources(
            cwfif_payload=cwfif_payload,
            lio_payload=lio_payload,
        )

    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "fire_source_reconciliation_failed",
                "message": str(error),
            },
        ) from error