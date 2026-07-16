import type {
    Feature,
    FeatureCollection,
    MultiPolygon,
    Polygon,
  } from "geojson";
  
  export interface AlertProperties {
    id: string;
    alert_code: string;
    alert_type: string;
    alert_name_en: string;
    alert_short_name_en: string;
    alert_text_en: string;
    publication_datetime: string;
    expiration_datetime: string | null;
    validity_datetime: string | null;
    event_end_datetime: string | null;
    risk_colour_en: string | null;
    confidence_en: string | null;
    impact_en: string | null;
    feature_name_en: string;
    province: string;
    status_en: string;
    feature_id: string;
  }
  
  export type AlertFeature = Feature<
    Polygon | MultiPolygon,
    AlertProperties
  >;
  
  export interface AlertFeatureCollection
    extends FeatureCollection<
      Polygon | MultiPolygon,
      AlertProperties
    > {
    source: string;
    source_url: string;
    retrieved_at: string;
    feature_count: number;
    official_wording_preserved: boolean;
  }