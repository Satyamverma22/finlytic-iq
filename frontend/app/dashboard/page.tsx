"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { listConsents } from "@/features/consent/api";

export default function DashboardPage() {
  const [needsConsent, setNeedsConsent] = useState(false);

  useEffect(() => {
    listConsents()
      .then((cs) => setNeedsConsent(!cs.some((c: any) => c.status === "active")))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {needsConsent && (
        <div className="border rounded-md p-4 text-sm">
          To use Financial Compass features, please review and grant consent in the{" "}
          <Link href="/dashboard/consent" className="underline">Consent Center</Link>.
        </div>
      )}
    </div>
  );
}