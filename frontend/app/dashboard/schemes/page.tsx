"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  schemeSearchSchema,
  type SchemeSearchFormInput,
  type SchemeSearchFormValues,
} from "@/lib/schemas/schemes";
import { matchSchemes } from "@/features/schemes/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function SchemesPage() {
  const [results, setResults] = useState<any[]>([]);
  const [searched, setSearched] = useState(false);
  const { register, handleSubmit, formState: { isSubmitting } } =
  useForm<SchemeSearchFormInput, any, SchemeSearchFormValues>({
    resolver: zodResolver(schemeSearchSchema),
  });

  const onSubmit = async (values: SchemeSearchFormValues) => {
    const payload = {
      ...values,
      target_groups: values.target_groups
        ? values.target_groups.split(",").map((s) => s.trim())
        : undefined,
    };
    const res = await matchSchemes(payload);
    setResults(res.results);
    setSearched(true);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold">Scheme Finder</h1>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div><Label>State</Label><Input {...register("state")} /></div>
            <div><Label>Occupation</Label><Input {...register("occupation")} /></div>
            <div><Label>Education level</Label><Input {...register("education_level")} /></div>
            <div><Label>Business type</Label><Input {...register("business_type")} /></div>
            <div><Label>Monthly income</Label><Input type="number" {...register("monthly_income")} /></div>
            <div><Label>Target groups (comma-separated)</Label><Input {...register("target_groups")} placeholder="student, woman" /></div>
            <div><Label>What are you looking for?</Label><Input {...register("query")} placeholder="help with tuition fees" /></div>
            <Button type="submit" disabled={isSubmitting}>Search</Button>
          </form>
        </CardContent>
      </Card>

      {searched && results.length === 0 && <p className="text-sm text-muted-foreground">No matching schemes found.</p>}

      {results.map((r) => (
        <Card key={r.scheme_id}>
          <CardHeader><CardTitle>{r.scheme_name} — {r.category}</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>{r.explanation}</p>
            <p><strong>Needs verification:</strong> {r.needs_verification.join(", ")}</p>
            <p><strong>Required documents:</strong> {r.required_documents?.join(", ") || "—"}</p>
            <p>
              <a href={r.official_url} target="_blank" className="text-blue-600 underline">
                Official source
              </a> — {r.department}, last verified {r.last_verified_date}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}