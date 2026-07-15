import json
from collections import Counter
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_DIR / "fixtures" / "cwfis-active-fires.json"

FIELDS_TO_INSPECT = [
    "agency_code",
    "region_code",
    "stage_of_control_status",
    "national_fire_cause",
    "response_type",
    "percent_contained",
]


def print_unique_values(features: list[dict], field: str) -> None:
    values = Counter(
        feature.get("properties", {}).get(field)
        for feature in features
    )

    print(f"\n{field}:")

    for value, count in sorted(
        values.items(),
        key=lambda item: str(item[0]),
    ):
        print(f"  {value}: {count}")


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "CWFIF fixture not found. Run "
            "`python -m src.fetch_cwfis` first."
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    features = payload.get("features", [])

    print(f"Total features: {len(features)}")

    geometry_types = Counter(
        feature.get("geometry", {}).get("type")
        for feature in features
    )

    print("\nGeometry types:")

    for geometry_type, count in geometry_types.items():
        print(f"  {geometry_type}: {count}")

    for field in FIELDS_TO_INSPECT:
        print_unique_values(features, field)

    missing_national_ids = sum(
        not feature.get("properties", {}).get("national_fire_id")
        for feature in features
    )

    missing_agency_ids = sum(
        not feature.get("properties", {}).get("agency_fire_id")
        for feature in features
    )

    missing_geometry = sum(
        not feature.get("geometry")
        for feature in features
    )

    print("\nMissing values:")
    print(f"  national_fire_id: {missing_national_ids}")
    print(f"  agency_fire_id: {missing_agency_ids}")
    print(f"  geometry: {missing_geometry}")


if __name__ == "__main__":
    main()