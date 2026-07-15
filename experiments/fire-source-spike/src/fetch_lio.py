import json
from datetime import datetime, timezone
from pathlib import Path

import httpx


LIO_QUERY_URL = (
    "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/"
    "LIO_OPEN_DATA/LIO_Open09/MapServer/51/query"
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_DIR / "fixtures"

DATA_FILE = FIXTURES_DIR / "lio-fire-perimeters.json"
METADATA_FILE = FIXTURES_DIR / "lio-fire-perimeters.metadata.json"


def fetch_fire_perimeters() -> dict:
    """Fetch Ontario's current in-year fire perimeters."""

    parameters = {
        "where": "1=1",
        "outFields": "*",
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
    }

    print("Fetching Ontario fire perimeters from LIO...")

    try:
        response = httpx.get(
            LIO_QUERY_URL,
            params=parameters,
            timeout=30.0,
            follow_redirects=True,
        )

        response.raise_for_status()

    except httpx.TimeoutException as error:
        raise RuntimeError(
            "LIO did not respond within 30 seconds."
        ) from error

    except httpx.HTTPStatusError as error:
        raise RuntimeError(
            f"LIO returned HTTP {error.response.status_code}: "
            f"{error.response.text[:500]}"
        ) from error

    except httpx.RequestError as error:
        raise RuntimeError(
            f"Could not connect to LIO: {error}"
        ) from error

    try:
        payload = response.json()

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "LIO returned a response that was not valid JSON."
        ) from error

    if "error" in payload:
        raise RuntimeError(
            f"LIO returned an ArcGIS error: {payload['error']}"
        )

    if payload.get("type") != "FeatureCollection":
        raise RuntimeError(
            "LIO response was not a GeoJSON FeatureCollection."
        )

    features = payload.get("features")

    if not isinstance(features, list):
        raise RuntimeError(
            "LIO response did not contain a valid features array."
        )

    return payload


def verify_response(payload: dict) -> None:
    """Perform basic validation without modifying the source response."""

    features = payload.get("features", [])

    geometry_types = sorted({
        feature.get("geometry", {}).get("type")
        for feature in features
        if feature.get("geometry")
    })

    missing_geometry = sum(
        not feature.get("geometry")
        for feature in features
    )

    missing_fire_numbers = sum(
        not feature.get("properties", {}).get("FIRENUMB")
        for feature in features
    )

    print(f"Received {len(features)} perimeters.")
    print(f"Geometry types: {geometry_types}")
    print(f"Missing geometry: {missing_geometry}")
    print(f"Missing fire numbers: {missing_fire_numbers}")


def save_response(payload: dict) -> None:
    """Save the source response and local retrieval metadata separately."""

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    metadata = {
        "source": "Ontario Land Information Ontario",
        "source_url": LIO_QUERY_URL,
        "layer": "In-year Fire Perimeters",
        "layer_id": 51,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "output_spatial_reference": "EPSG:4326",
        "feature_count": len(payload.get("features", [])),
    }

    with METADATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )


def print_first_feature(payload: dict) -> None:
    features = payload.get("features", [])

    if not features:
        print("No perimeter features were returned.")
        return

    first_feature = features[0]
    geometry = first_feature.get("geometry") or {}
    properties = first_feature.get("properties") or {}

    print("\nFirst feature geometry:")
    print(geometry.get("type"))

    print("\nFirst feature properties:")

    for key, value in properties.items():
        print(f"  {key}: {value}")


def main() -> None:
    payload = fetch_fire_perimeters()

    verify_response(payload)
    save_response(payload)
    print_first_feature(payload)

    print(f"\nSaved data to: {DATA_FILE}")
    print(f"Saved metadata to: {METADATA_FILE}")


if __name__ == "__main__":
    main()
    