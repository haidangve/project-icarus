import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]

FIXTURES_DIR = PROJECT_DIR / "fixtures"
OUTPUT_DIR = PROJECT_DIR / "output"

CWFIF_FILE = FIXTURES_DIR / "cwfis-active-fires.json"
LIO_FILE = FIXTURES_DIR / "lio-fire-perimeters.json"

OUTPUT_FILE = OUTPUT_DIR / "combined-active-fires.geojson"
METADATA_FILE = OUTPUT_DIR / "combined-active-fires.metadata.json"


def load_geojson(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing source fixture: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"{path.name} is not a GeoJSON FeatureCollection.")

    return payload


def lio_number_to_agency_id(fire_number: str) -> str | None:
    match = re.fullmatch(
        r"([A-Z]{3})(\d+)",
        fire_number.strip().upper(),
    )

    if not match:
        return None

    region, number = match.groups()

    return f"{region}_FIRE_{int(number):03d}"


def build_lio_index(features: list[dict]) -> dict[str, dict]:
    """
    Index eligible interim LIO perimeters by their expected CWFIF agency ID.

    If several perimeters exist for one fire, retain the latest DATE_MAPPED.
    """

    index: dict[str, dict] = {}

    for feature in features:
        properties = feature.get("properties", {})

        if properties.get("STATUS") != "I":
            continue

        if properties.get("FIRETYPE") != "IFR":
            continue

        fire_number = properties.get("FIRENUMB")

        if not fire_number:
            continue

        agency_fire_id = lio_number_to_agency_id(fire_number)

        if agency_fire_id is None:
            continue

        existing = index.get(agency_fire_id)

        if existing is None:
            index[agency_fire_id] = feature
            continue

        existing_date = (
            existing.get("properties", {}).get("DATE_MAPPED") or 0
        )

        candidate_date = properties.get("DATE_MAPPED") or 0

        if candidate_date > existing_date:
            index[agency_fire_id] = feature

    return index


def reconcile_feature(
    cwfif_feature: dict,
    lio_index: dict[str, dict],
) -> dict:
    cwfif_properties = cwfif_feature.get("properties", {})
    agency_fire_id = cwfif_properties.get("agency_fire_id")

    lio_feature = lio_index.get(agency_fire_id)

    reported_point = cwfif_feature.get("geometry")

    properties = {
        "national_fire_id": cwfif_properties.get("national_fire_id"),
        "agency_fire_id": agency_fire_id,
        "agency_code": cwfif_properties.get("agency_code"),
        "region_code": cwfif_properties.get("region_code"),
        "fire_size": cwfif_properties.get("fire_size"),
        "stage_of_control_status": cwfif_properties.get(
            "stage_of_control_status"
        ),
        "national_fire_cause": cwfif_properties.get(
            "national_fire_cause"
        ),
        "response_type": cwfif_properties.get("response_type"),
        "situation_report_date": cwfif_properties.get(
            "situation_report_date"
        ),
        "status_date": cwfif_properties.get("status_date"),
        "reported_point": reported_point,
        "incident_source": "CWFIF",
    }

    if lio_feature:
        lio_properties = lio_feature.get("properties", {})

        properties.update({
            "geometry_source": "LIO",
            "has_official_perimeter": True,
            "lio_fire_number": lio_properties.get("FIRENUMB"),
            "lio_current_size": lio_properties.get("CUR_SIZE"),
            "lio_status": lio_properties.get("STATUS"),
            "lio_fire_type": lio_properties.get("FIRETYPE"),
            "lio_reference": lio_properties.get("REFERENCE"),
            "lio_date_mapped": lio_properties.get("DATE_MAPPED"),
        })

        geometry = lio_feature.get("geometry")

    else:
        properties.update({
            "geometry_source": "CWFIF",
            "has_official_perimeter": False,
            "lio_fire_number": None,
            "lio_current_size": None,
            "lio_status": None,
            "lio_fire_type": None,
            "lio_reference": None,
            "lio_date_mapped": None,
        })

        geometry = reported_point

    return {
        "type": "Feature",
        "id": cwfif_properties.get("national_fire_id"),
        "geometry": geometry,
        "properties": properties,
    }


def main() -> None:
    cwfif_payload = load_geojson(CWFIF_FILE)
    lio_payload = load_geojson(LIO_FILE)

    cwfif_features = cwfif_payload.get("features", [])
    lio_features = lio_payload.get("features", [])

    lio_index = build_lio_index(lio_features)

    combined_features = [
        reconcile_feature(feature, lio_index)
        for feature in cwfif_features
    ]

    perimeter_count = sum(
        feature["properties"]["has_official_perimeter"]
        for feature in combined_features
    )

    point_count = len(combined_features) - perimeter_count

    combined_payload = {
        "type": "FeatureCollection",
        "features": combined_features,
    }

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_active_fires": len(combined_features),
        "fires_with_lio_perimeters": perimeter_count,
        "fires_with_cwfif_points_only": point_count,
        "matching_method": "Exact transformed agency_fire_id",
        "active_status_source": "CWFIF",
        "perimeter_source": "LIO",
        "spatial_or_fuzzy_matching_used": False,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            combined_payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    with METADATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Active fires: {len(combined_features)}")
    print(f"With LIO perimeter: {perimeter_count}")
    print(f"With CWFIF point only: {point_count}")
    print(f"Saved GeoJSON to: {OUTPUT_FILE}")
    print(f"Saved metadata to: {METADATA_FILE}")


if __name__ == "__main__":
    main()