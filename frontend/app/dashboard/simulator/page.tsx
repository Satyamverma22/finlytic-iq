"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  scenarioSchema,
  type ScenarioFormInput,
  type ScenarioFormValues,
} from "@/lib/schemas/credit";
import { createScenario, listScenarios } from "@/features/credit/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function SimulatorPage() {
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ScenarioFormInput, any, ScenarioFormValues>({
    resolver: zodResolver(scenarioSchema),
  });
  
  const loadHistory = async () => {
    const res = await listScenarios();
    setHistory(res.items);
  };

  useEffect(() => { loadHistory(); }, []);

  const onSubmit = async (values: ScenarioFormValues) => {
    setError(null);
    try {
      const scenario = await createScenario(values);
      setResult(scenario);
      await loadHistory();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold">What-If Simulator</h1>

      <Card>
        <CardHeader><CardTitle>New scenario</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div>
              <Label>Label</Label>
              <Input {...register("label")} placeholder="e.g. New Car Loan" />
            </div>
            <div>
              <Label>Loan amount</Label>
              <Input type="number" step="0.01" {...register("proposed_amount")} />
            </div>
            <div>
              <Label>Annual interest rate (%)</Label>
              <Input type="number" step="0.01" {...register("annual_interest_rate")} />
            </div>
            <div>
              <Label>Tenure (months)</Label>
              <Input type="number" {...register("tenure_months")} />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" disabled={isSubmitting}>Simulate</Button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader><CardTitle>Result: {result.label}</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p>Estimated EMI: ₹{result.estimated_emi}</p>
            <p>Total interest: ₹{result.total_interest}</p>
            <p>Resulting DTI: {(result.resulting_dti * 100).toFixed(1)}%</p>
            <p>Remaining monthly cash flow: ₹{result.remaining_cash_flow}</p>
            <p><strong>Risk: {result.risk_category}</strong></p>
            <ul className="list-disc ml-5">
              {result.risk_factors.map((f: string, i: number) => <li key={i}>{f}</li>)}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Past scenarios</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {history.map((s) => (
              <li key={s.id} className="flex justify-between border-b pb-1">
                <span>{s.label}</span>
                <span>{s.risk_category} — ₹{s.estimated_emi}/mo</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}