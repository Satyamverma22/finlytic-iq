import { apiFetch } from "@/lib/api-client";

export const listConsents = () => apiFetch<any[]>("/api/consents");
export const grantConsent = (purpose: string) =>
  apiFetch<any>("/api/consents", { method: "POST", body: JSON.stringify({ purpose }) });
export const revokeConsent = (id: string) =>
  apiFetch<any>(`/api/consents/${id}/revoke`, { method: "PATCH" });