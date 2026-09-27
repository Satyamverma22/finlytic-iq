import { apiFetch } from "@/lib/api-client";
import type { ScenarioFormValues } from "@/lib/schemas/credit";

export const createScenario = (payload: ScenarioFormValues) =>
  apiFetch<any>("/api/credit-scenarios", { method: "POST", body: JSON.stringify(payload) });

export const listScenarios = () => apiFetch<any>("/api/credit-scenarios");