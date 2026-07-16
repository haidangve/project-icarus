import type { FireFeature } from "@/types/fire";

interface FireDetailsProps {
  fire: FireFeature | null;
  generatedAt: string;
  onClose: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  OC: "Out of control",
  BH: "Being held",
  UC: "Under control",
};

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "Unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unavailable";
  }

  return date.toLocaleString("en-CA", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

function formatSize(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "Unavailable";
  }

  return `${value.toLocaleString("en-CA", {
    maximumFractionDigits: 1,
  })} ha`;
}

export default function FireDetails({
  fire,
  generatedAt,
  onClose,
}: FireDetailsProps) {
  if (!fire) {
    return null;
  }

  const properties = fire.properties;
  const statusCode =
    properties.stage_of_control_status ?? "";

  const status =
    STATUS_LABELS[statusCode] ??
    statusCode ??
    "Status unavailable";

  const size =
    properties.lio_current_size ??
    properties.fire_size;

  return (
    <aside
      className="fire-details"
      aria-labelledby="fire-details-title"
    >
      <button
        type="button"
        className="fire-details__close"
        onClick={onClose}
        aria-label="Close fire details"
      >
        ×
      </button>

      <div className="fire-details__official">
        Official incident information
      </div>

      <p className="fire-details__eyebrow">
        {properties.agency_fire_id}
      </p>

      <h2 id="fire-details-title">
        {properties.region_code
          ? `${properties.region_code} wildfire`
          : "Ontario wildfire"}
      </h2>

      <div
        className={`fire-details__status fire-details__status--${statusCode.toLowerCase()}`}
      >
        {status}
        {statusCode && <span>{statusCode}</span>}
      </div>

      <dl className="fire-details__facts">
        <div>
          <dt>National fire ID</dt>
          <dd>{properties.national_fire_id}</dd>
        </div>

        <div>
          <dt>Reported size</dt>
          <dd>{formatSize(size)}</dd>
        </div>

        <div>
          <dt>Map representation</dt>
          <dd>
            {properties.has_official_perimeter
              ? "Official Ontario perimeter"
              : "Reported incident point"}
          </dd>
        </div>

        <div>
          <dt>Official status time</dt>
          <dd>{formatDate(properties.status_date)}</dd>
        </div>

        <div>
          <dt>Situation report time</dt>
          <dd>
            {formatDate(properties.situation_report_date)}
          </dd>
        </div>

        <div>
          <dt>Data retrieved</dt>
          <dd>{formatDate(generatedAt)}</dd>
        </div>
      </dl>

      <div className="fire-details__sources">
        <strong>Sources</strong>

        <p>
          Incident information: Canadian Wildland Fire
          Information Framework
        </p>

        <p>
          Geometry:{" "}
          {properties.has_official_perimeter
            ? "Land Information Ontario"
            : "CWFIF reported location"}
        </p>
      </div>

      <p className="fire-details__warning">
        Situational awareness only. Conditions may change
        quickly. Follow evacuation orders and instructions from
        official emergency authorities.
      </p>
    </aside>
  );
}