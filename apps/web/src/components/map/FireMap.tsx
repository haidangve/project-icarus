"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, {
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";

import AlertDetails from "@/components/alerts/AlertDetails";
import FireDetails from "@/components/fires/FireDetails";
import { getAlerts } from "@/lib/api/alerts";
import { getFires } from "@/lib/api/fires";
import type {
  AlertFeature,
  AlertFeatureCollection,
} from "@/types/alert";
import type {
  FireFeature,
  FireFeatureCollection,
} from "@/types/fire";

const EMPTY_FIRES: FireFeatureCollection = {
  type: "FeatureCollection",
  features: [],
  generated_at: "",
  feature_count: 0,
  perimeter_count: 0,
  point_only_count: 0,
};

const EMPTY_ALERTS: AlertFeatureCollection = {
  type: "FeatureCollection",
  features: [],
  source: "",
  source_url: "",
  retrieved_at: "",
  feature_count: 0,
  official_wording_preserved: true,
};

function createMapSafeAlerts(
  alerts: AlertFeatureCollection,
): AlertFeatureCollection {
  return {
    ...alerts,
    features: alerts.features.map((feature) => {
      const { id: _mapLibreUnsafeId, ...safeFeature } =
        feature;

      return safeFeature;
    }),
  };
}

export default function FireMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);

  const firesRef =
    useRef<FireFeatureCollection>(EMPTY_FIRES);
  const alertsRef =
    useRef<AlertFeatureCollection>(EMPTY_ALERTS);

  const [fires, setFires] =
    useState<FireFeatureCollection>(EMPTY_FIRES);
  const [alerts, setAlerts] =
    useState<AlertFeatureCollection>(EMPTY_ALERTS);

  const [selectedFire, setSelectedFire] =
    useState<FireFeature | null>(null);
  const [selectedAlert, setSelectedAlert] =
    useState<AlertFeature | null>(null);

  const [fireError, setFireError] =
    useState<string | null>(null);
  const [alertError, setAlertError] =
    useState<string | null>(null);

  useEffect(() => {
    getFires()
      .then((data) => {
        firesRef.current = data;
        setFires(data);

        const source = mapRef.current?.getSource(
          "fires",
        ) as GeoJSONSource | undefined;

        source?.setData(data);
      })
      .catch((error: unknown) => {
        setFireError(
          error instanceof Error
            ? error.message
            : "Unable to load current fires.",
        );
      });

    getAlerts()
      .then((data) => {
        alertsRef.current = data;
        setAlerts(data);

        const source = mapRef.current?.getSource(
          "official-alerts",
        ) as GeoJSONSource | undefined;

        source?.setData(createMapSafeAlerts(data));
      })
      .catch((error: unknown) => {
        setAlertError(
          error instanceof Error
            ? error.message
            : "Unable to load official alerts.",
        );
      });
  }, []);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [-85, 49],
      zoom: 4.5,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
          },
        ],
      },
    });

    map.addControl(
      new maplibregl.NavigationControl(),
      "top-right",
    );

    map.on("load", () => {
      map.addSource("official-alerts", {
        type: "geojson",
        data: createMapSafeAlerts(alertsRef.current),
      });

      map.addLayer({
        id: "official-alert-fill",
        type: "fill",
        source: "official-alerts",
        paint: {
          "fill-color": [
            "match",
            ["downcase", ["coalesce", ["get", "risk_colour_en"], ""]],
            "red",
            "#c9302c",
            "orange",
            "#f26a2e",
            "yellow",
            "#f2c94c",
            "#76867c",
          ],
          "fill-opacity": 0.18,
        },
      });

      map.addLayer({
        id: "official-alert-outline",
        type: "line",
        source: "official-alerts",
        paint: {
          "line-color": [
            "match",
            ["downcase", ["coalesce", ["get", "risk_colour_en"], ""]],
            "red",
            "#9e1f1b",
            "orange",
            "#c94d19",
            "yellow",
            "#a98200",
            "#59675f",
          ],
          "line-width": 1.5,
          "line-dasharray": [3, 2],
        },
      });

      map.addSource("fires", {
        type: "geojson",
        data: firesRef.current,
      });

      map.addLayer({
        id: "fire-perimeter-fill",
        type: "fill",
        source: "fires",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["Polygon", "MultiPolygon"]],
        ],
        paint: {
          "fill-color": "#f26a2e",
          "fill-opacity": 0.35,
        },
      });

      map.addLayer({
        id: "fire-perimeter-outline",
        type: "line",
        source: "fires",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["Polygon", "MultiPolygon"]],
        ],
        paint: {
          "line-color": "#a83e19",
          "line-width": 2.5,
        },
      });

      map.addLayer({
        id: "fire-points",
        type: "circle",
        source: "fires",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            4,
            5,
            10,
            10,
          ],
          "circle-color": [
            "match",
            ["get", "stage_of_control_status"],
            "OC",
            "#d9471f",
            "BH",
            "#f5a33b",
            "UC",
            "#49a078",
            "#718078",
          ],
          "circle-stroke-color": "#fff9ef",
          "circle-stroke-width": 1.5,
        },
      });

      const interactiveLayers = [
        "fire-points",
        "fire-perimeter-outline",
        "fire-perimeter-fill",
        "official-alert-outline",
        "official-alert-fill",
      ];
      
      map.on("click", (event) => {
        const renderedFeatures = map.queryRenderedFeatures(
          event.point,
          {
            layers: interactiveLayers,
          },
        );
      
        const fireMapFeature = renderedFeatures.find(
          (feature) =>
            feature.layer.id === "fire-points" ||
            feature.layer.id === "fire-perimeter-outline" ||
            feature.layer.id === "fire-perimeter-fill",
        );
      
        if (fireMapFeature) {
          const nationalFireId =
            fireMapFeature.properties?.national_fire_id;
      
          const fire = firesRef.current.features.find(
            (candidate) =>
              candidate.properties.national_fire_id ===
              nationalFireId,
          );
      
          if (fire) {
            setSelectedFire(fire);
            setSelectedAlert(null);
            return;
          }
        }
      
        const alertMapFeature = renderedFeatures.find(
          (feature) =>
            feature.layer.id === "official-alert-fill" ||
            feature.layer.id === "official-alert-outline",
        );
      
        if (alertMapFeature) {
          const alertId = alertMapFeature.properties?.id;
      
          const alert = alertsRef.current.features.find(
            (candidate) =>
              candidate.properties.id === alertId,
          );
      
          if (alert) {
            setSelectedAlert(alert);
            setSelectedFire(null);
          }
        }
      });
      
      map.on("mousemove", (event) => {
        const renderedFeatures = map.queryRenderedFeatures(
          event.point,
          {
            layers: interactiveLayers,
          },
        );
      
        map.getCanvas().style.cursor =
          renderedFeatures.length > 0 ? "pointer" : "";
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  return (
    <section className="map-shell">
      <div className="map-summary">
        <strong>{fires.feature_count || "—"}</strong>
        <span>active Ontario fires</span>

        <small>
          {fires.perimeter_count} official perimeters
        </small>

        <small>
          {alerts.feature_count} official alert regions
        </small>
      </div>

      {(fireError || alertError) && (
        <div className="map-error" role="alert">
          {fireError || alertError}
        </div>
      )}

      <div
        ref={containerRef}
        className="fire-map"
        aria-label="Map of Ontario wildfires and official weather alerts"
      />

      <FireDetails
        fire={selectedFire}
        generatedAt={fires.generated_at}
        onClose={() => setSelectedFire(null)}
      />

      <AlertDetails
        alert={selectedAlert}
        retrievedAt={alerts.retrieved_at}
        onClose={() => setSelectedAlert(null)}
      />
    </section>
  );
}