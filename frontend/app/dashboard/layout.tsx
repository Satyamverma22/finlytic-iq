"use client";
import { useAuthGuard } from "@/hooks/use-auth-guard";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const ready = useAuthGuard();
  if (!ready) return null;
  return <div className="p-6">{children}</div>;
}