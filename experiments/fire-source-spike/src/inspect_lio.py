import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_DIR / "fixtures" / "lio-fire-perimeters.json"

FIELDS_TO_INSPECT = [
    "STATUS",
    "FIRETYPE",
    "REFERENCE",
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
        print(f"  {repr(value)}: {count}")


def convert_arcgis_date(value: int | None) -> str | None:
    """Convert ArcGIS epoch milliseconds to an ISO 8601 UTC timestamp."""

    if value is None:
        return None

    return datetime.fromtimestamp(
        value / 1000,
        tz=timezone.utc,
    ).isoformat()


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "LIO fixture not found. Run "
            "`python -m src.fetch_lio` first."
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    features = payload.get("features", [])

    print(f"Total LIO perimeters: {len(features)}")

    geometry_types = Counter(
        feature.get("geometry", {}).get("type")
        for feature in features
    )

    print("\nGeometry types:")

    for geometry_type, count in geometry_types.items():
        print(f"  {geometry_type}: {count}")

    for field in FIELDS_TO_INSPECT:
        print_unique_values(features, field)

    dates = [
        feature.get("properties", {}).get("DATE_MAPPED")
        for feature in features
        if feature.get("properties", {}).get("DATE_MAPPED") is not None
    ]

    print("\nDATE_MAPPED:")

    if dates:
        print(f"  Earliest: {convert_arcgis_date(min(dates))}")
        print(f"  Latest: {convert_arcgis_date(max(dates))}")
    else:
        print("  No mapping dates found.")

    unusual_fire_numbers = [
        feature.get("properties", {}).get("FIRENUMB")
        for feature in features
        if "_FIRE_" not in str(
            feature.get("properties", {}).get("FIRENUMB")
        )
        and not str(
            feature.get("properties", {}).get("FIRENUMB")
        ).isalnum()
    ]

    print("\nUnusual fire numbers:")

    for fire_number in unusual_fire_numbers:
        print(f"  {fire_number}")


if __name__ == "__main__":
    main()