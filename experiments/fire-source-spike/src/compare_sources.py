import json
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_DIR / "fixtures"

CWFIF_FILE = FIXTURES_DIR / "cwfis-active-fires.json"
LIO_FILE = FIXTURES_DIR / "lio-fire-perimeters.json"


def load_features(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing fixture: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return payload.get("features", [])


def lio_number_to_agency_id(fire_number: str) -> str | None:
    """
    Convert an LIO fire number such as COC008 into the expected
    CWFIF agency identifier COC_FIRE_008.
    """

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

    cwfif_ids = {
        feature.get("properties", {}).get("agency_fire_id")
        for feature in cwfif_features
        if feature.get("properties", {}).get("agency_fire_id")
    }

    matched = []
    unmatched = []
    invalid = []

    for feature in lio_features:
        properties = feature.get("properties", {})
        fire_number = properties.get("FIRENUMB")

        if not fire_number:
            invalid.append(None)
            continue

        expected_agency_id = lio_number_to_agency_id(fire_number)

        if expected_agency_id is None:
            invalid.append(fire_number)
            continue

        result = {
            "lio_fire_number": fire_number,
            "expected_cwfif_id": expected_agency_id,
        }

        if expected_agency_id in cwfif_ids:
            matched.append(result)
        else:
            unmatched.append(result)

    lio_expected_ids = {
        result["expected_cwfif_id"]
        for result in matched + unmatched
    }

    cwfif_without_lio = sorted(cwfif_ids - lio_expected_ids)

    print(f"CWFIF active-fire points: {len(cwfif_features)}")
    print(f"LIO fire perimeters: {len(lio_features)}")

    print(f"\nExact identifier matches: {len(matched)}")
    print(f"Unmatched LIO perimeters: {len(unmatched)}")
    print(f"Invalid LIO fire numbers: {len(invalid)}")
    print(f"CWFIF fires without LIO perimeters: {len(cwfif_without_lio)}")

    if unmatched:
        print("\nUnmatched LIO perimeters:")

        for item in unmatched:
            print(
                f"  {item['lio_fire_number']} -> "
                f"{item['expected_cwfif_id']}"
            )

    if invalid:
        print("\nInvalid LIO fire numbers:")

        for fire_number in invalid:
            print(f"  {fire_number}")

    if cwfif_without_lio:
        print("\nFirst 20 CWFIF fires without LIO perimeters:")

        for agency_fire_id in cwfif_without_lio[:20]:
            print(f"  {agency_fire_id}")


if __name__ == "__main__":
    main()