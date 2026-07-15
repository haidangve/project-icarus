import json
from collections import Counter
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = (
    PROJECT_DIR
    / "output"
    / "combined-active-fires.geojson"
)


def main() -> None:
    with OUTPUT_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if payload.get("type") != "FeatureCollection":
        raise ValueError("Output is not a GeoJSON FeatureCollection.")

    features = payload.get("features", [])

    ids = [feature.get("id") for feature in features]
    duplicate_ids = [
        fire_id
        for fire_id, count in Counter(ids).items()
        if count > 1
    ]

    missing_ids = sum(not fire_id for fire_id in ids)
    missing_geometry = sum(
        not feature.get("geometry")
        for feature in features
    )

    perimeter_features = [
        feature
        for feature in features
        if feature.get("properties", {}).get(
            "has_official_perimeter"
        )
    ]

    point_features = [
        feature
        for feature in features
        if not feature.get("properties", {}).get(
            "has_official_perimeter"
        )
    ]

    invalid_perimeter_geometry = [
        feature.get("id")
        for feature in perimeter_features
        if feature.get("geometry", {}).get("type")
        not in {"Polygon", "MultiPolygon"}
    ]

    invalid_point_geometry = [
        feature.get("id")
        for feature in point_features
        if feature.get("geometry", {}).get("type") != "Point"
    ]

    missing_reported_points = sum(
        not feature.get("properties", {}).get("reported_point")
        for feature in features
    )

    print(f"Total features: {len(features)}")
    print(f"Perimeter features: {len(perimeter_features)}")
    print(f"Point-only features: {len(point_features)}")
    print(f"Missing IDs: {missing_ids}")
    print(f"Duplicate IDs: {len(duplicate_ids)}")
    print(f"Missing geometry: {missing_geometry}")
    print(f"Missing reported points: {missing_reported_points}")
    print(
        "Invalid perimeter geometry: "
        f"{len(invalid_perimeter_geometry)}"
    )
    print(
        "Invalid point geometry: "
        f"{len(invalid_point_geometry)}"
    )

    errors = (
        missing_ids
        + len(duplicate_ids)
        + missing_geometry
        + missing_reported_points
        + len(invalid_perimeter_geometry)
        + len(invalid_point_geometry)
    )

    if errors:
        raise RuntimeError(
            f"Combined dataset failed validation with {errors} errors."
        )

    print("\nCombined dataset validation passed.")


if __name__ == "__main__":
    main()