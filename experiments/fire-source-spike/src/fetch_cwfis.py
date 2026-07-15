import json
from datetime import datetime, timezone
from pathlib import Path

import httpx


CWFIF_WFS_URL = "https://geoserver.cwfif.nrcan.gc.ca/geoserver/wfs"
CWFIF_COLLECTION = "public:cwfif_national_activefires"

# Select only current Ontario records.
CWFIF_FILTER = (
    "agency_code='ON' "
    "AND now()>=record_start "
    "AND now()<=record_end"
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_DIR / "fixtures"

DATA_FILE = FIXTURES_DIR / "cwfis-active-fires.json"
METADATA_FILE = FIXTURES_DIR / "cwfis-active-fires.metadata.json"


def fetch_active_fires() -> dict:
    """Fetch current agency-reported active fires in Ontario."""

    parameters = {
        "service": "WFS",
        "version": "2.0.1",
        "request": "GetFeature",
        "typeName": CWFIF_COLLECTION,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "CQL_FILTER": CWFIF_FILTER,
    }

    print("Fetching current Ontario active fires from CWFIF...")

    try:
        response = httpx.get(
            CWFIF_WFS_URL,
            params=parameters,
            timeout=30.0,
            follow_redirects=True,
        )

        response.raise_for_status()

    except httpx.TimeoutException as error:
        raise RuntimeError(
            "CWFIF did not respond within 30 seconds."
        ) from error

    except httpx.HTTPStatusError as error:
        response_preview = error.response.text[:500]

        raise RuntimeError(
            f"CWFIF returned HTTP {error.response.status_code}: "
            f"{response_preview}"
        ) from error

    except httpx.RequestError as error:
        raise RuntimeError(
            f"Could not connect to CWFIF: {error}"
        ) from error

    try:
        payload = response.json()

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "CWFIF returned a response that was not valid JSON."
        ) from error

    if payload.get("type") != "FeatureCollection":
        raise RuntimeError(
            "CWFIF response was not a GeoJSON FeatureCollection."
        )

    features = payload.get("features")

    if not isinstance(features, list):
        raise RuntimeError(
            "CWFIF response did not contain a valid features array."
        )

    return payload


def save_response(payload: dict) -> None:
    """Save the filtered source response and retrieval metadata separately."""

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Preserve the server response without adding local fields or changing
    # source property names and geometries.
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    retrieval_metadata = {
        "source": "Natural Resources Canada — CWFIF",
        "source_url": CWFIF_WFS_URL,
        "collection": CWFIF_COLLECTION,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "server_filter": CWFIF_FILTER,
        "feature_count": len(payload.get("features", [])),
    }

    with METADATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            retrieval_metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )


def print_summary(payload: dict) -> None:
    """Print a small schema and record summary."""

    features = payload.get("features", [])

    print(f"Received {len(features)} features.")
    print(f"Saved data to: {DATA_FILE}")
    print(f"Saved metadata to: {METADATA_FILE}")

    if not features:
        print("The response contained no current Ontario active fires.")
        return

    first_feature = features[0]
    geometry = first_feature.get("geometry") or {}
    properties = first_feature.get("properties") or {}

    print("\nFirst feature ID:")
    print(first_feature.get("id"))

    print("\nFirst feature geometry type:")
    print(geometry.get("type"))

    print("\nFirst feature coordinates:")
    print(geometry.get("coordinates"))

    print("\nFirst feature property keys:")

    for key in sorted(properties.keys()):
        print(f"  - {key}")

    print("\nFirst feature important values:")

    important_fields = [
        "national_fire_id",
        "agency_fire_id",
        "agency_code",
        "region_code",
        "fire_size",
        "stage_of_control_status",
        "percent_contained",
        "national_fire_cause",
        "response_type",
        "situation_report_date",
        "status_date",
        "record_start",
        "record_end",
    ]

    for field in important_fields:
        print(f"  {field}: {properties.get(field)}")


def verify_ontario_records(payload: dict) -> None:
    """Confirm that the server filter returned only Ontario records."""

    features = payload.get("features", [])

    agency_codes = {
        feature.get("properties", {}).get("agency_code")
        for feature in features
    }

    print("\nAgency codes in response:")
    print(sorted(str(code) for code in agency_codes))

    non_ontario_features = [
        feature
        for feature in features
        if feature.get("properties", {}).get("agency_code") != "ON"
    ]

    if non_ontario_features:
        raise RuntimeError(
            "CWFIF returned records outside Ontario despite the server filter. "
            f"Unexpected record count: {len(non_ontario_features)}"
        )

    print("Ontario agency verification passed.")


def verify_geometry(payload: dict) -> None:
    """Report the geometry types returned by CWFIF."""

    features = payload.get("features", [])

    geometry_types = {
        feature.get("geometry", {}).get("type")
        for feature in features
        if feature.get("geometry")
    }

    print("\nGeometry types in response:")
    print(sorted(str(geometry_type) for geometry_type in geometry_types))

    missing_geometry = [
        feature.get("id")
        for feature in features
        if not feature.get("geometry")
    ]

    if missing_geometry:
        print(
            f"Warning: {len(missing_geometry)} features have no geometry."
        )

    if geometry_types == {"Point"}:
        print("Geometry verification passed: all geometries are Points.")
    else:
        print(
            "Warning: the response contains geometry types other than Point."
        )


def main() -> None:
    payload = fetch_active_fires()

    verify_ontario_records(payload)
    verify_geometry(payload)
    save_response(payload)
    print_summary(payload)


if __name__ == "__main__":
    main()