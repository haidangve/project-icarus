import re
from datetime import datetime, timezone
from typing import Any

from app.schemas.fire import (
    FireFeature,
    FireFeatureCollection,
    FireProperties,
)


def lio_number_to_agency_id(fire_number: str) -> str | None:
    """
    Convert an LIO fire number into a CWFIF agency fire ID.

    Example:
        COC008 -> COC_FIRE_008
    """

    match = re.fullmatch(
        r"([A-Z]{3})(\d+)",
        fire_number.strip().upper(),
    )

    if not match:
        return None

    region, number = match.groups()

    return f"{region}_FIRE_{int(number):03d}"


def arcgis_milliseconds_to_datetime(
    value: int | float | None,
) -> datetime | None:
    """Convert an ArcGIS epoch-millisecond value into UTC."""

    if value is None:
        return None

    return datetime.fromtimestamp(
        value / 1000,
        tz=timezone.utc,
    )


def non_negative_number(value: Any) -> float | None:
    """
    Convert a source number into a non-negative float.

    Negative sentinel values become None.
    """

    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number < 0:
        return None

    return number


def build_lio_index(
    features: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Index eligible LIO perimeters by their expected CWFIF agency ID.

    Only interim in-year fire perimeters participate in reconciliation.
    When several eligible perimeters exist, retain the latest mapped version.
    """

    index: dict[str, dict[str, Any]] = {}

    for feature in features:
        properties = feature.get("properties", {})

        if properties.get("STATUS") != "I":
            continue

        if properties.get("FIRETYPE") != "IFR":
            continue

        fire_number = properties.get("FIRENUMB")

        if not isinstance(fire_number, str):
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


def reconcile_fire(
    cwfif_feature: dict[str, Any],
    lio_index: dict[str, dict[str, Any]],
) -> FireFeature:
    """Create one normalized active-fire feature."""

    cwfif_properties = cwfif_feature.get("properties", {})

    national_fire_id = cwfif_properties.get("national_fire_id")
    agency_fire_id = cwfif_properties.get("agency_fire_id")
    agency_code = cwfif_properties.get("agency_code")

    if not isinstance(national_fire_id, str):
        raise ValueError("CWFIF fire is missing national_fire_id.")

    if not isinstance(agency_fire_id, str):
        raise ValueError(
            f"CWFIF fire {national_fire_id} is missing agency_fire_id."
        )

    if not isinstance(agency_code, str):
        raise ValueError(
            f"CWFIF fire {national_fire_id} is missing agency_code."
        )

    reported_point = cwfif_feature.get("geometry")

    if not isinstance(reported_point, dict):
        raise ValueError(
            f"CWFIF fire {national_fire_id} is missing point geometry."
        )

    lio_feature = lio_index.get(agency_fire_id)

    if lio_feature is not None:
        lio_properties = lio_feature.get("properties", {})
        geometry = lio_feature.get("geometry")

        if not isinstance(geometry, dict):
            raise ValueError(
                f"LIO perimeter for {agency_fire_id} has no geometry."
            )

        geometry_source = "LIO"
        has_official_perimeter = True

        lio_fire_number = lio_properties.get("FIRENUMB")
        lio_current_size = non_negative_number(
            lio_properties.get("CUR_SIZE")
        )
        lio_status = lio_properties.get("STATUS")
        lio_fire_type = lio_properties.get("FIRETYPE")
        lio_reference = lio_properties.get("REFERENCE")
        lio_date_mapped = arcgis_milliseconds_to_datetime(
            lio_properties.get("DATE_MAPPED")
        )

    else:
        geometry = reported_point

        geometry_source = "CWFIF"
        has_official_perimeter = False

        lio_fire_number = None
        lio_current_size = None
        lio_status = None
        lio_fire_type = None
        lio_reference = None
        lio_date_mapped = None

    properties = FireProperties(
        national_fire_id=national_fire_id,
        agency_fire_id=agency_fire_id,
        agency_code=agency_code,
        region_code=cwfif_properties.get("region_code"),
        fire_size=non_negative_number(
            cwfif_properties.get("fire_size")
        ),
        stage_of_control_status=cwfif_properties.get(
            "stage_of_control_status"
        ),
        national_fire_cause=cwfif_properties.get(
            "national_fire_cause"
        ),
        response_type=cwfif_properties.get("response_type"),
        situation_report_date=cwfif_properties.get(
            "situation_report_date"
        ),
        status_date=cwfif_properties.get("status_date"),
        reported_point=reported_point,
        incident_source="CWFIF",
        geometry_source=geometry_source,
        has_official_perimeter=has_official_perimeter,
        lio_fire_number=lio_fire_number,
        lio_current_size=lio_current_size,
        lio_status=lio_status,
        lio_fire_type=lio_fire_type,
        lio_reference=lio_reference,
        lio_date_mapped=lio_date_mapped,
    )

    return FireFeature(
        id=national_fire_id,
        geometry=geometry,
        properties=properties,
    )


def reconcile_fire_sources(
    cwfif_payload: dict[str, Any],
    lio_payload: dict[str, Any],
) -> FireFeatureCollection:
    """Combine current CWFIF incidents with exact-match LIO perimeters."""

    cwfif_features = cwfif_payload.get("features", [])
    lio_features = lio_payload.get("features", [])

    if not isinstance(cwfif_features, list):
        raise ValueError("CWFIF payload has no features list.")

    if not isinstance(lio_features, list):
        raise ValueError("LIO payload has no features list.")

    lio_index = build_lio_index(lio_features)

    combined_features = [
        reconcile_fire(feature, lio_index)
        for feature in cwfif_features
    ]

    perimeter_count = sum(
        feature.properties.has_official_perimeter
        for feature in combined_features
    )

    point_only_count = len(combined_features) - perimeter_count

    return FireFeatureCollection(
        features=combined_features,
        generated_at=datetime.now(timezone.utc),
        feature_count=len(combined_features),
        perimeter_count=perimeter_count,
        point_only_count=point_only_count,
    )