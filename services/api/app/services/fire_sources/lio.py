from typing import Any

import httpx


LIO_QUERY_URL = (
    "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/"
    "LIO_OPEN_DATA/LIO_Open09/MapServer/51/query"
)

REQUEST_TIMEOUT_SECONDS = 30.0
VALID_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}


class LIOSourceError(RuntimeError):
    """Raised when LIO cannot provide valid fire-perimeter data."""


def _request_parameters() -> dict[str, str]:
    return {
        "where": "1=1",
        "outFields": "*",
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
    }


def _validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise LIOSourceError(
            "LIO returned a response that was not a JSON object."
        )

    if "error" in payload:
        raise LIOSourceError(
            f"LIO returned an ArcGIS error: {payload['error']}"
        )

    if payload.get("type") != "FeatureCollection":
        raise LIOSourceError(
            "LIO response was not a GeoJSON FeatureCollection."
        )

    features = payload.get("features")

    if not isinstance(features, list):
        raise LIOSourceError(
            "LIO response did not contain a features array."
        )

    missing_fire_numbers = sum(
        not feature.get("properties", {}).get("FIRENUMB")
        for feature in features
    )

    if missing_fire_numbers:
        raise LIOSourceError(
            f"LIO returned {missing_fire_numbers} records "
            "without fire numbers."
        )

    missing_geometry = sum(
        not feature.get("geometry")
        for feature in features
    )

    if missing_geometry:
        raise LIOSourceError(
            f"LIO returned {missing_geometry} records without geometry."
        )

    invalid_geometry_types = {
        feature.get("geometry", {}).get("type")
        for feature in features
        if feature.get("geometry", {}).get("type")
        not in VALID_GEOMETRY_TYPES
    }

    if invalid_geometry_types:
        raise LIOSourceError(
            "LIO returned unsupported geometry types: "
            f"{sorted(str(value) for value in invalid_geometry_types)}"
        )

    return payload


async def fetch_in_year_fire_perimeters(
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """
    Fetch Ontario in-year fire perimeters from LIO.

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
        raise LIOSourceError("Failed to initialize the HTTP client.")

    try:
        response = await client.get(
            LIO_QUERY_URL,
            params=_request_parameters(),
        )

        response.raise_for_status()

    except httpx.TimeoutException as error:
        raise LIOSourceError(
            "LIO did not respond within 30 seconds."
        ) from error

    except httpx.HTTPStatusError as error:
        response_preview = error.response.text[:500]

        raise LIOSourceError(
            f"LIO returned HTTP {error.response.status_code}: "
            f"{response_preview}"
        ) from error

    except httpx.RequestError as error:
        raise LIOSourceError(
            f"Could not connect to LIO: {error}"
        ) from error

    try:
        payload = response.json()

    except ValueError as error:
        raise LIOSourceError(
            "LIO returned a response that was not valid JSON."
        ) from error

    finally:
        if owns_client:
            await client.aclose()

    return _validate_payload(payload)