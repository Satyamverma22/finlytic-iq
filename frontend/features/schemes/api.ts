import { apiFetch } from "@/lib/api-client";

export const matchSchemes = (payload: any) =>
  apiFetch<any>("/api/schemes/match", { method: "POST", body: JSON.stringify(payload) });