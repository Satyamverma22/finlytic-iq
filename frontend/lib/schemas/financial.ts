import { z } from "zod";

export const profileSchema = z.object({
  monthly_income: z.coerce.number().positive(),
  liquid_savings: z.coerce.number().min(0),
  emergency_fund_target_months: z.coerce.number().int().min(1).max(24),
});

export type ProfileFormInput = z.input<typeof profileSchema>;
export type ProfileFormValues = z.output<typeof profileSchema>;