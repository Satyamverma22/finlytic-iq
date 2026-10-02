"use client";
import { useEffect, useState } from "react";
import { listConsents, grantConsent, revokeConsent } from "@/features/consent/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const PURPOSES = [
  { key: "financial_analysis", label: "Financial Analysis", desc: "Lets us process your transactions, income, loans and savings for health reports and loan simulations." },
  { key: "fraud_analysis", label: "Fraud Analysis", desc: "Lets us analyse messages you submit for scam warning signs." },
  { key: "personalised_recommendations", label: "Personalised Recommendations", desc: "Lets us use your profile details to match government schemes." },
  { key: "anonymous_analytics", label: "Anonymous Analytics", desc: "Optional. Allows use of anonymised, aggregated data. Not used by any feature yet." },
];

export default function ConsentPage() {
  const [consents, setConsents] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => setConsents(await listConsents());
  useEffect(() => { load(); }, []);

  const activeFor = (key: string) =>
    consents.find((c) => c.purpose === key && c.status === "active");

  const toggle = async (key: string) => {
    setError(null);
    try {
      const active = activeFor(key);
      if (active) await revokeConsent(active.id);
      else await grantConsent(key);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="space-y-4 max-w-2xl">
      <h1 className="text-2xl font-semibold">Consent Center</h1>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {PURPOSES.map((p) => {
        const active = activeFor(p.key);
        return (
          <Card key={p.key}>
            <CardHeader><CardTitle>{p.label}</CardTitle></CardHeader>
            <CardContent className="flex items-center justify-between gap-4 text-sm">
              <p>{p.desc}</p>
              <Button variant={active ? "outline" : "default"} onClick={() => toggle(p.key)}>
                {active ? "Revoke" : "Grant"}
              </Button>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}