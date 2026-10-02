import { apiFetch } from "@/lib/api-client";

export const analyseText = (payload: { input_type: string; text: string }) =>
  apiFetch<any>("/api/fraud/analyse-text", { method: "POST", body: JSON.stringify(payload) });

export const listScans = () => apiFetch<any>("/api/fraud/scans");