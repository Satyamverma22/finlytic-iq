"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  profileSchema,
  ProfileFormInput,
  ProfileFormValues,
} from "@/lib/schemas/financial";
import { getProfile, upsertProfile, getFinancialHealth, uploadCsv } from "@/features/financial/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function HealthPage() {
  const [health, setHealth] = useState<any>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } =
  useForm<ProfileFormInput, any, ProfileFormValues>({
  resolver: zodResolver(profileSchema),
  });
  const loadHealth = async () => {
    try {
      setHealth(await getFinancialHealth());
      setHealthError(null);
    } catch (e: any) {
      setHealth(null);
      setHealthError(e.message);
    }
  };

  useEffect(() => {
    getProfile().then((p) => reset(p)).catch(() => {});
    loadHealth();
  }, []);

  const onSaveProfile = async (values: ProfileFormValues) => {
    await upsertProfile(values);
    await loadHealth();
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const result = await uploadCsv(file);
    setUploadResult(result);
    await loadHealth();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold">Financial Health</h1>

      <Card>
        <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSaveProfile)} className="space-y-3">
            <div>
              <Label>Monthly income</Label>
              <Input type="number" step="0.01" {...register("monthly_income")} />
              {errors.monthly_income && <p className="text-sm text-red-500">{errors.monthly_income.message}</p>}
            </div>
            <div>
              <Label>Liquid savings</Label>
              <Input type="number" step="0.01" {...register("liquid_savings")} />
            </div>
            <div>
              <Label>Emergency fund target (months)</Label>
              <Input type="number" {...register("emergency_fund_target_months")} />
            </div>
            <Button type="submit" disabled={isSubmitting}>Save profile</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Upload transactions CSV</CardTitle></CardHeader>
        <CardContent>
          <Input type="file" accept=".csv" onChange={onUpload} />
          {uploadResult && (
            <p className="text-sm mt-2">
              Stored {uploadResult.rows_stored} of {uploadResult.rows_received} rows
              ({uploadResult.duplicates_skipped} duplicates, {uploadResult.rows_failed} failed).
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Health Report</CardTitle></CardHeader>
        <CardContent>
          {healthError && <p className="text-sm text-muted-foreground">{healthError}</p>}
          {health && (
            <div className="space-y-2 text-sm">
              <p><strong>Category:</strong> {health.category}</p>
              <p>Savings ratio: {(health.savings_ratio * 100).toFixed(1)}%</p>
              <p>DTI: {(health.dti * 100).toFixed(1)}%</p>
              <div>
                <strong>Positive factors</strong>
                <ul className="list-disc ml-5">{health.positive_factors.map((f: string, i: number) => <li key={i}>{f}</li>)}</ul>
              </div>
              <div>
                <strong>Risk factors</strong>
                <ul className="list-disc ml-5">{health.risk_factors.map((f: string, i: number) => <li key={i}>{f}</li>)}</ul>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}