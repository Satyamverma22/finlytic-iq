"use client";
import { useEffect, useState } from "react";
import { analyseText, listScans } from "@/features/fraud/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const INPUT_TYPES = [
  "sms", "email", "whatsapp", "url", "upi_id",
  "investment_offer", "call_transcript", "payment_request",
];

const RISK_COLORS: Record<string, string> = {
  Low: "text-green-600",
  Medium: "text-amber-600",
  High: "text-red-600",
};

export default function FraudPage() {
  const [inputType, setInputType] = useState("sms");
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => setHistory((await listScans()).items);
  useEffect(() => { loadHistory(); }, []);

  const onAnalyse = async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await analyseText({ input_type: inputType, text }));
      await loadHistory();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold">Fraud Protection</h1>

      <Card>
        <CardContent className="pt-6 space-y-3">
          <div>
            <Label>Message type</Label>
            <select
              value={inputType}
              onChange={(e) => setInputType(e.target.value)}
              className="w-full border rounded-md h-9 px-2 text-sm bg-background"
            >
              {INPUT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <Label>Message text</Label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
              maxLength={5000}
              className="w-full border rounded-md p-2 text-sm bg-background"
              placeholder="Paste the suspicious message here..."
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button onClick={onAnalyse} disabled={loading || !text.trim()}>
            {loading ? "Analysing..." : "Analyse"}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>
              Risk: <span className={RISK_COLORS[result.risk_level]}>{result.risk_level}</span>
              {result.scam_category && ` — ${result.scam_category}`}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {result.detected_signals.length > 0 && (
              <div>
                <strong>Warning signs detected</strong>
                <ul className="list-disc ml-5">
                  {result.detected_signals.map((s: string, i: number) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
            {result.urls_found.length > 0 && (
              <p><strong>Links found:</strong> {result.urls_found.join(", ")}</p>
            )}
            <p>{result.explanation}</p>
            <p><strong>Recommended action:</strong> {result.recommended_action}</p>
            <p className="text-xs text-muted-foreground">
              This is an automated analysis, not a guarantee that a message is safe or fraudulent.
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Recent scans</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-1 text-sm">
            {history.map((s) => (
              <li key={s.id} className="flex justify-between border-b pb-1">
                <span>{s.input_type} — {new Date(s.created_at).toLocaleString()}</span>
                <span className={RISK_COLORS[s.risk_level]}>{s.risk_level}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}