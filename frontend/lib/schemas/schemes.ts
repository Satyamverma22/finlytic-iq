import { z } from "zod";

export const schemeSearchSchema = z.object({
  state: z.string().optional(),
  occupation: z.string().optional(),
  education_level: z.string().optional(),
  business_type: z.string().optional(),
  monthly_income: z.coerce.number().optional(),
  target_groups: z.string().optional(),
  query: z.string().optional(),
});

export type SchemeSearchFormInput = z.input<typeof schemeSearchSchema>;
export type SchemeSearchFormValues = z.output<typeof schemeSearchSchema>;