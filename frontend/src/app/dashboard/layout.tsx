"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Settings, ShieldCheck } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

/**
 * Shared chrome for every /dashboard/* route: brand, signed-in user, Settings
 * link, and Sign out. Keeps auth-session UI in one place instead of repeated
 * on every page.
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [email, setEmail] = useState<string | null>(null);
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setEmail(data.user?.email ?? null));
  }, [supabase]);

  async function signOut() {
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
            <ShieldCheck className="h-5 w-5" />
            AuditAgent
          </Link>
          <div className="flex items-center gap-4">
            {email && <span className="text-sm text-muted-foreground">{email}</span>}
            <Link
              href="/dashboard/settings"
              className={`flex items-center gap-1.5 text-sm font-medium hover:text-foreground ${
                pathname === "/dashboard/settings" ? "text-foreground" : "text-muted-foreground"
              }`}
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
            <Button variant="outline" size="sm" onClick={signOut}>
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
