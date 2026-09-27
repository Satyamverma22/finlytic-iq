import { z } from "zod";

export const scenarioSchema = z.object({
  label: z.string().min(1).max(255),
  proposed_amount: z.coerce.number().positive(),
  annual_interest_rate: z.coerce.number().min(0).max(100),
  tenure_months: z.coerce.number().int().positive(),
});

export type ScenarioFormInput = z.input<typeof scenarioSchema>;
export type ScenarioFormValues = z.output<typeof scenarioSchema>;