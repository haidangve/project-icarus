import type {
    AlertFeatureCollection,
  } from "@/types/alert";
  
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";
  
  export async function getAlerts(): Promise<AlertFeatureCollection> {
    const response = await fetch(`${API_URL}/alerts`, {
      cache: "no-store",
    });
  
    if (!response.ok) {
      throw new Error(
        `Unable to load official alerts: HTTP ${response.status}`,
      );
    }
  
    return response.json() as Promise<AlertFeatureCollection>;
  }