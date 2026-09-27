import { apiFetch, apiUpload } from "@/lib/api-client";
import type { ProfileFormValues } from "@/lib/schemas/financial";

export const getProfile = () => apiFetch<any>("/api/financial/profile");
export const upsertProfile = (payload: ProfileFormValues) =>
  apiFetch<any>("/api/financial/profile", { method: "PUT", body: JSON.stringify(payload) });
export const getFinancialHealth = () => apiFetch<any>("/api/financial/health");
export const uploadCsv = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload<any>("/api/transactions/upload", formData);
};