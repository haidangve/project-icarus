from typing import Any

import httpx


CWFIF_WFS_URL = "https://geoserver.cwfif.nrcan.gc.ca/geoserver/wfs"
CWFIF_COLLECTION = "public:cwfif_national_activefires"

CWFIF_FILTER = (
    "agency_code='ON' "
    "AND now()>=record_start "
    "AND now()<=record_end"
)

REQUEST_TIMEOUT_SECONDS = 30.0


class CWFIFSourceError(RuntimeError):
    """Raised when the CWFIF source cannot provide valid fire data."""


def _request_parameters() -> dict[str, str]:
    return {
        "service": "WFS",
        "version": "2.0.1",
        "request": "GetFeature",
        "typeName": CWFIF_COLLECTION,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "CQL_FILTER": CWFIF_FILTER,
    }


def _validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CWFIFSourceError(
            "CWFIF returned a response that was not a JSON object."
        )

    if payload.get("type") != "FeatureCollection":
        raise CWFIFSourceError(
            "CWFIF response was not a GeoJSON FeatureCollection."
        )

    features = payload.get("features")

    if not isinstance(features, list):
        raise CWFIFSourceError(
            "CWFIF response did not contain a features array."
        )

    invalid_agencies = {
        feature.get("properties", {}).get("agency_code")
        for feature in features
        if feature.get("properties", {}).get("agency_code") != "ON"
    }

    if invalid_agencies:
        raise CWFIFSourceError(
            "CWFIF returned non-Ontario records: "
            f"{sorted(str(code) for code in invalid_agencies)}"
        )

    missing_ids = sum(
        not feature.get("properties", {}).get("national_fire_id")
        or not feature.get("properties", {}).get("agency_fire_id")
        for feature in features
    )

    if missing_ids:
        raise CWFIFSourceError(
            f"CWFIF returned {missing_ids} records with missing fire IDs."
        )

    return payload


async def fetch_current_ontario_fires(
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """
    Fetch current agency-reported Ontario fires from CWFIF.

    The returned payload is source GeoJSON. It is validated but not normalized
    or modified.
    """

    owns_client = client is None

    if owns_client:
        client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )

    if client is None:
        raise CWFIFSourceError("Failed to initialize the HTTP client.")

    try:
        response = await client.get(
            CWFIF_WFS_URL,
            params=_request_parameters(),
        )

        response.raise_for_status()

    except httpx.TimeoutException as error:
        raise CWFIFSourceError(
            "CWFIF did not respond within 30 seconds."
        ) from error

    except httpx.HTTPStatusError as error:
        response_preview = error.response.text[:500]

        raise CWFIFSourceError(
            f"CWFIF returned HTTP {error.response.status_code}: "
            f"{response_preview}"
        ) from error

    except httpx.RequestError as error:
        raise CWFIFSourceError(
            f"Could not connect to CWFIF: {error}"
        ) from error

    try:
        payload = response.json()

    except ValueError as error:
        raise CWFIFSourceError(
            "CWFIF returned a response that was not valid JSON."
        ) from error

    finally:
        if owns_client:
            await client.aclose()

    return _validate_payload(payload)