import type {
    Feature,
    FeatureCollection,
    Geometry,
    Point,
  } from "geojson";
  
  export type FireGeometrySource = "CWFIF" | "LIO";
  
  export type FireControlStatus = "OC" | "BH" | "UC" | string;
  
  export interface FireProperties {
    national_fire_id: string;
    agency_fire_id: string;
    agency_code: string;
    region_code: string | null;
  
    fire_size: number | null;
    stage_of_control_status: FireControlStatus | null;
    national_fire_cause: string | null;
    response_type: string | null;
  
    situation_report_date: string | null;
    status_date: string | null;
  
    reported_point: Point;
  
    incident_source: "CWFIF";
    geometry_source: FireGeometrySource;
    has_official_perimeter: boolean;
  
    lio_fire_number: string | null;
    lio_current_size: number | null;
    lio_status: string | null;
    lio_fire_type: string | null;
    lio_reference: string | null;
    lio_date_mapped: string | null;
  }
  
  export type FireFeature = Feature<Geometry, FireProperties> & {
    id: string;
  };
  
  export interface FireFeatureCollection
    extends FeatureCollection<Geometry, FireProperties> {
    generated_at: string;
    feature_count: number;
    perimeter_count: number;
    point_only_count: number;
  }
  
  export function hasOfficialPerimeter(
    fire: FireFeature,
  ): boolean {
    return (
      fire.properties.has_official_perimeter &&
      (
        fire.geometry.type === "Polygon" ||
        fire.geometry.type === "MultiPolygon"
      )
    );
  }
  
  export function isPointOnlyFire(
    fire: FireFeature,
  ): boolean {
    return (
      !fire.properties.has_official_perimeter &&
      fire.geometry.type === "Point"
    );
  }