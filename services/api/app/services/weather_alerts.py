from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import (
    ECCC_ALERTS_TIMEOUT_SECONDS,
    ECCC_ALERTS_URL,
    ONTARIO_PROVINCE_CODE,
)


async def fetch_ontario_weather_alerts() -> dict[str, Any]:
    params = {
        "f": "json",
        "limit": 10000,
        "filter": (
            f"properties.province="
            f"{ONTARIO_PROVINCE_CODE}"
        ),
    }

    try:
        async with httpx.AsyncClient(
            timeout=ECCC_ALERTS_TIMEOUT_SECONDS,
        ) as client:
            response = await client.get(
                ECCC_ALERTS_URL,
                params=params,
                headers={
                    "Accept": "application/geo+json",
                    "User-Agent": "Icarus/0.1",
                },
            )

            response.raise_for_status()

    except httpx.TimeoutException as error:
        raise RuntimeError(
            "Environment Canada alerts request timed out "
            f"after {ECCC_ALERTS_TIMEOUT_SECONDS} seconds."
        ) from error

    except httpx.HTTPStatusError as error:
        body = error.response.text[:500]

        raise RuntimeError(
            "Environment Canada alerts returned "
            f"HTTP {error.response.status_code}: {body}"
        ) from error

    except httpx.RequestError as error:
        raise RuntimeError(
            "Unable to connect to Environment Canada alerts."
        ) from error

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            "Environment Canada returned invalid JSON."
        ) from error

    if payload.get("type") != "FeatureCollection":
        raise RuntimeError(
            "Environment Canada response is not a "
            "GeoJSON FeatureCollection."
        )

    features = payload.get("features")

    if not isinstance(features, list):
        raise RuntimeError(
            "Environment Canada response has no valid "
            "features array."
        )

    # Preserve all official feature geometries and properties.
    # Only add retrieval metadata at the collection level.
    payload["source"] = (
        "Environment and Climate Change Canada — MSC GeoMet"
    )
    payload["source_url"] = ECCC_ALERTS_URL
    payload["retrieved_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    payload["feature_count"] = len(features)
    payload["official_wording_preserved"] = True

    return payload