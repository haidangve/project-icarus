from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


GeoJSONGeometry = dict[str, Any]


class FireProperties(BaseModel):
    """Normalized properties returned for an active fire."""

    model_config = ConfigDict(extra="forbid")

    national_fire_id: str
    agency_fire_id: str
    agency_code: str
    region_code: str | None = None

    fire_size: float | None = Field(
        default=None,
        ge=0,
        description="Agency-reported fire size. Units require source confirmation.",
    )

    stage_of_control_status: str | None = None
    national_fire_cause: str | None = None
    response_type: str | None = None

    situation_report_date: datetime | None = None
    status_date: datetime | None = None

    reported_point: GeoJSONGeometry

    incident_source: Literal["CWFIF"]
    geometry_source: Literal["CWFIF", "LIO"]
    has_official_perimeter: bool

    lio_fire_number: str | None = None
    lio_current_size: float | None = Field(default=None, ge=0)
    lio_status: str | None = None
    lio_fire_type: str | None = None
    lio_reference: str | None = None
    lio_date_mapped: datetime | None = None


class FireFeature(BaseModel):
    """One active fire represented as a GeoJSON feature."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: GeoJSONGeometry
    properties: FireProperties


class FireFeatureCollection(BaseModel):
    """GeoJSON response returned by GET /fires."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[FireFeature]
    generated_at: datetime
    feature_count: int = Field(ge=0)
    perimeter_count: int = Field(ge=0)
    point_only_count: int = Field(ge=0)