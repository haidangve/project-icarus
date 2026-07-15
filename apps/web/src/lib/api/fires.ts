import type { FireFeatureCollection } from "@/types/fire";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getFires(): Promise<FireFeatureCollection> {
  const response = await fetch(`${API_URL}/fires`);

  if (!response.ok) {
    throw new Error(
      `Fire API returned ${response.status}: ${response.statusText}`,
    );
  }

  const payload: unknown = await response.json();

  if (
    !payload ||
    typeof payload !== "object" ||
    !("type" in payload) ||
    !("features" in payload) ||
    payload.type !== "FeatureCollection" ||
    !Array.isArray(payload.features)
  ) {
    throw new Error("Fire API returned an invalid GeoJSON response.");
  }

  return payload as FireFeatureCollection;
}