"use client";
import { useAuthGuard } from "@/hooks/use-auth-guard";
import { DashboardNav } from "@/components/dashboard-nav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const ready = useAuthGuard();
  if (!ready) return null;

  return (
    <div className="flex">
      <DashboardNav />
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}