from fastapi.testclient import TestClient

from app.main import app
from app.routers import fires as fires_router


client = TestClient(app)


CWFIF_FIXTURE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "cwfif-point-1",
            "geometry": {
                "type": "Point",
                "coordinates": [-89.0, 49.0],
            },
            "properties": {
                "national_fire_id": "2026_ON_COC_FIRE_008",
                "agency_fire_id": "COC_FIRE_008",
                "agency_code": "ON",
                "region_code": "COC",
                "fire_size": 100,
                "stage_of_control_status": "OC",
                "national_fire_cause": "N",
                "response_type": "FUL",
                "situation_report_date": "2026-07-15T12:00:00Z",
                "status_date": "2026-07-15T13:00:00Z",
            },
        },
        {
            "type": "Feature",
            "id": "cwfif-point-2",
            "geometry": {
                "type": "Point",
                "coordinates": [-90.0, 50.0],
            },
            "properties": {
                "national_fire_id": "2026_ON_THU_FIRE_058",
                "agency_fire_id": "THU_FIRE_058",
                "agency_code": "ON",
                "region_code": "THU",
                "fire_size": 6,
                "stage_of_control_status": "BH",
                "national_fire_cause": "H",
                "response_type": "MON",
                "situation_report_date": "2026-07-15T12:00:00Z",
                "status_date": "2026-07-15T13:00:00Z",
            },
        },
    ],
}


LIO_FIXTURE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-89.1, 48.9],
                        [-88.9, 48.9],
                        [-88.9, 49.1],
                        [-89.1, 48.9],
                    ]
                ],
            },
            "properties": {
                "OBJECTID": 1,
                "FIRENUMB": "COC008",
                "CUR_SIZE": 100.5,
                "REFERENCE": "Test perimeter",
                "FIRETYPE": "IFR",
                "STATUS": "I",
                "DATE_MAPPED": 1784138400000,
            },
        }
    ],
}


async def fake_fetch_cwfif(*args, **kwargs) -> dict:
    return CWFIF_FIXTURE


async def fake_fetch_lio(*args, **kwargs) -> dict:
    return LIO_FIXTURE


def test_fires_endpoint_reconciles_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        fires_router,
        "fetch_current_ontario_fires",
        fake_fetch_cwfif,
    )

    monkeypatch.setattr(
        fires_router,
        "fetch_in_year_fire_perimeters",
        fake_fetch_lio,
    )

    response = client.get("/fires")

    assert response.status_code == 200

    payload = response.json()

    assert payload["type"] == "FeatureCollection"
    assert payload["feature_count"] == 2
    assert payload["perimeter_count"] == 1
    assert payload["point_only_count"] == 1
    assert len(payload["features"]) == 2

    perimeter_fire = payload["features"][0]

    assert perimeter_fire["id"] == "2026_ON_COC_FIRE_008"
    assert perimeter_fire["geometry"]["type"] == "Polygon"
    assert perimeter_fire["properties"]["geometry_source"] == "LIO"
    assert perimeter_fire["properties"]["has_official_perimeter"] is True
    assert (
        perimeter_fire["properties"]["reported_point"]["type"]
        == "Point"
    )

    point_fire = payload["features"][1]

    assert point_fire["id"] == "2026_ON_THU_FIRE_058"
    assert point_fire["geometry"]["type"] == "Point"
    assert point_fire["properties"]["geometry_source"] == "CWFIF"
    assert point_fire["properties"]["has_official_perimeter"] is False