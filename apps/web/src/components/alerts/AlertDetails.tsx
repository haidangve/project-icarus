import type { AlertFeature } from "@/types/alert";

interface AlertDetailsProps {
  alert: AlertFeature | null;
  retrievedAt: string;
  onClose: () => void;
}

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

export default function AlertDetails({
  alert,
  retrievedAt,
  onClose,
}: AlertDetailsProps) {
  if (!alert) {
    return null;
  }

  const properties = alert.properties;
  const riskColour =
    properties.risk_colour_en?.toLowerCase() ??
    "unknown";

  return (
    <aside
      className="alert-details"
      aria-labelledby="alert-details-title"
    >
      <button
        type="button"
        className="alert-details__close"
        onClick={onClose}
        aria-label="Close official alert"
      >
        ×
      </button>

      <div className="alert-details__official">
        Official Environment Canada alert
      </div>

      <p className="alert-details__area">
        {properties.feature_name_en}
      </p>

      <h2 id="alert-details-title">
        {properties.alert_name_en}
      </h2>

      <div
        className={`alert-details__risk alert-details__risk--${riskColour}`}
      >
        {properties.risk_colour_en
          ? `${properties.risk_colour_en} ${properties.alert_type}`
          : properties.alert_type}
      </div>

      <dl className="alert-details__facts">
        <div>
          <dt>Impact</dt>
          <dd>{properties.impact_en || "Unavailable"}</dd>
        </div>

        <div>
          <dt>Confidence</dt>
          <dd>
            {properties.confidence_en || "Unavailable"}
          </dd>
        </div>

        <div>
          <dt>Published</dt>
          <dd>
            {formatDate(properties.publication_datetime)}
          </dd>
        </div>

        <div>
          <dt>Expires</dt>
          <dd>
            {formatDate(properties.expiration_datetime)}
          </dd>
        </div>

        <div>
          <dt>Data retrieved</dt>
          <dd>{formatDate(retrievedAt)}</dd>
        </div>
      </dl>

      <section className="alert-details__wording">
        <h3>Official alert wording</h3>

        <p>{properties.alert_text_en}</p>
      </section>

      <p className="alert-details__source">
        Source: Environment and Climate Change Canada,
        Meteorological Service of Canada
      </p>

      <p className="alert-details__warning">
        This is a weather alert, not a wildfire evacuation
        order. Follow instructions issued by emergency
        authorities.
      </p>
    </aside>
  );
}