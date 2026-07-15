"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, {
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";

import FireDetails from "@/components/fires/FireDetails";
import { getFires } from "@/lib/api/fires";
import type {
  FireFeature,
  FireFeatureCollection,
} from "@/types/fire";

const EMPTY_COLLECTION: FireFeatureCollection = {
  type: "FeatureCollection",
  features: [],
  generated_at: "",
  feature_count: 0,
  perimeter_count: 0,
  point_only_count: 0,
};

export default function FireMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);

  const [fires, setFires] =
    useState<FireFeatureCollection>(EMPTY_COLLECTION);

  const [selectedFire, setSelectedFire] =
    useState<FireFeature | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getFires()
      .then(setFires)
      .catch((requestError: unknown) => {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load current fires.",
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
      map.addSource("fires", {
        type: "geojson",
        data: EMPTY_COLLECTION,
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
          "fill-opacity": 0.28,
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
          "line-width": 2,
        },
      });

      map.addLayer({
        id: "fire-points",
        type: "circle",
        source: "fires",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-radius": 6,
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
    });

    const selectFire = (
      event: maplibregl.MapLayerMouseEvent,
    ) => {
      const nationalFireId =
        event.features?.[0]?.properties?.national_fire_id;

      const fire = fires.features.find(
        (candidate) =>
          candidate.properties.national_fire_id === nationalFireId,
      );

      if (fire) {
        setSelectedFire(fire);
      }
    };

    const interactiveLayers = [
      "fire-perimeter-fill",
      "fire-perimeter-outline",
      "fire-points",
    ];

    interactiveLayers.forEach((layer) => {
      map.on("click", layer, selectFire);

      map.on("mouseenter", layer, () => {
        map.getCanvas().style.cursor = "pointer";
      });

      map.on("mouseleave", layer, () => {
        map.getCanvas().style.cursor = "";
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [fires.features]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map || !map.isStyleLoaded()) {
      return;
    }

    const source = map.getSource("fires") as
      | GeoJSONSource
      | undefined;

    source?.setData(fires);
  }, [fires]);

  return (
    <section className="map-shell">
      <div className="map-summary">
        <strong>{fires.feature_count}</strong>
        <span>active Ontario fires</span>

        <small>
          {fires.perimeter_count} official perimeters
        </small>
      </div>

      {error && (
        <div className="map-error" role="alert">
          {error}
        </div>
      )}

      <div
        ref={containerRef}
        className="fire-map"
        aria-label="Map of active Ontario wildfires"
      />

      <FireDetails
        fire={selectedFire}
        onClose={() => setSelectedFire(null)}
      />
    </section>
  );
}