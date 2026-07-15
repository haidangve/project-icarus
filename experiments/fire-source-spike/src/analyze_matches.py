import json
import re
from collections import Counter
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_DIR / "fixtures"

CWFIF_FILE = FIXTURES_DIR / "cwfis-active-fires.json"
LIO_FILE = FIXTURES_DIR / "lio-fire-perimeters.json"


def load_features(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file).get("features", [])


def convert_lio_id(fire_number: str) -> str | None:
    match = re.fullmatch(
        r"([A-Z]{3})(\d+)",
        fire_number.strip().upper(),
    )

    if not match:
        return None

    region, number = match.groups()

    return f"{region}_FIRE_{int(number):03d}"


def main() -> None:
    cwfif_features = load_features(CWFIF_FILE)
    lio_features = load_features(LIO_FILE)

    cwfif_by_id = {
        feature["properties"]["agency_fire_id"]: feature
        for feature in cwfif_features
    }

    matched_statuses = Counter()
    unmatched_statuses = Counter()
    matched_fire_types = Counter()
    unmatched_fire_types = Counter()
    matched_control_statuses = Counter()

    for feature in lio_features:
        properties = feature.get("properties", {})

        fire_number = properties.get("FIRENUMB", "")
        lio_status = properties.get("STATUS")
        fire_type = properties.get("FIRETYPE")

        expected_id = convert_lio_id(fire_number)

        if expected_id and expected_id in cwfif_by_id:
            matched_statuses[lio_status] += 1
            matched_fire_types[fire_type] += 1

            cwfif_properties = cwfif_by_id[expected_id]["properties"]

            matched_control_statuses[
                cwfif_properties.get("stage_of_control_status")
            ] += 1

        else:
            unmatched_statuses[lio_status] += 1
            unmatched_fire_types[fire_type] += 1

    print("Matched LIO STATUS values:")

    for value, count in matched_statuses.items():
        print(f"  {value}: {count}")

    print("\nUnmatched LIO STATUS values:")

    for value, count in unmatched_statuses.items():
        print(f"  {value}: {count}")

    print("\nMatched LIO FIRETYPE values:")

    for value, count in matched_fire_types.items():
        print(f"  {value}: {count}")

    print("\nUnmatched LIO FIRETYPE values:")

    for value, count in unmatched_fire_types.items():
        print(f"  {value}: {count}")

    print("\nCWFIF control status for matched fires:")

    for value, count in matched_control_statuses.items():
        print(f"  {value}: {count}")


if __name__ == "__main__":
    main()