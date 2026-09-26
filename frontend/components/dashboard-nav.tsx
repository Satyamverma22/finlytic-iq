"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth-token";
import { Button } from "@/components/ui/button";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/health", label: "Financial Health" },
  { href: "/dashboard/simulator", label: "What-If Simulator" },
  { href: "/dashboard/schemes", label: "Scheme Finder" },
  { href: "/dashboard/fraud", label: "Fraud Protection" },
  { href: "/dashboard/copilot", label: "AI Copilot" },
];

export function DashboardNav() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    clearToken();
    router.push("/login");
  };

  return (
    <nav className="w-56 shrink-0 border-r h-screen p-4 flex flex-col justify-between">
      <div className="space-y-1">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`block px-3 py-2 rounded-md text-sm ${
              pathname === link.href ? "bg-muted font-medium" : "hover:bg-muted"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </div>
      <Button variant="outline" onClick={logout}>Log out</Button>
    </nav>
  );
}