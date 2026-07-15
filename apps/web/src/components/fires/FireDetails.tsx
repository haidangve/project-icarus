import type { FireFeature } from "@/types/fire";

interface FireDetailsProps {
  fire: FireFeature | null;
  onClose: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  OC: "Out of control",
  BH: "Being held",
  UC: "Under control",
};

export default function FireDetails({
  fire,
  onClose,
}: FireDetailsProps) {
  if (!fire) {
    return null;
  }

  const properties = fire.properties;

  const status =
    STATUS_LABELS[properties.stage_of_control_status ?? ""] ??
    properties.stage_of_control_status ??
    "Status unavailable";

  const size =
    properties.lio_current_size ??
    properties.fire_size;

  return (
    <aside className="fire-details">
      <button
        className="fire-details__close"
        onClick={onClose}
        aria-label="Close fire details"
      >
        ×
      </button>

      <p className="fire-details__eyebrow">
        {properties.agency_fire_id}
      </p>

      <h2>{properties.region_code} wildfire</h2>

      <dl>
        <div>
          <dt>Status</dt>
          <dd>{status}</dd>
        </div>

        <div>
          <dt>Reported size</dt>
          <dd>
            {size !== null
              ? `${size.toLocaleString()} ha`
              : "Unavailable"}
          </dd>
        </div>

        <div>
          <dt>Geometry</dt>
          <dd>
            {properties.has_official_perimeter
              ? "Official LIO perimeter"
              : "Reported CWFIF point"}
          </dd>
        </div>

        <div>
          <dt>Status time</dt>
          <dd>
            {properties.status_date
              ? new Date(properties.status_date).toLocaleString()
              : "Unavailable"}
          </dd>
        </div>
      </dl>

      <p className="fire-details__source">
        Incident: CWFIF · Geometry: {properties.geometry_source}
      </p>

      <p className="fire-details__warning">
        Situational awareness only. Follow instructions from official
        emergency authorities.
      </p>
    </aside>
  );
}
