import Link from "next/link";

import { env } from "@/lib/env";

/**
 * Phase 1 landing / system-status page.
 * Server Component: pings the FastAPI backend so you can visually confirm the
 * whole stack is wired before building the dashboard (Phase 3).
 */
async function getBackendStatus() {
  try {
    const res = await fetch(`${env.backendUrl}/health/db`, {
      cache: "no-store",
    });
    if (!res.ok) return { ok: false, detail: `HTTP ${res.status}` };
    return { ok: true, detail: await res.json() };
  } catch {
    return { ok: false, detail: "backend unreachable" };
  }
}

export default async function Home() {
  const status = await getBackendStatus();

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6">
      <div>
        <span className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Phase 1 · Foundation
        </span>
        <h1 className="mt-4 text-4xl font-bold tracking-tight">AuditAgent</h1>
        <p className="mt-2 text-muted-foreground">
          Multi-agent AI compliance monitoring & audit automation for SOC 2 and HIPAA.
        </p>
      </div>

      <div className="rounded-lg border bg-card p-5 text-card-foreground">
        <h2 className="text-sm font-semibold text-muted-foreground">System status</h2>
        <ul className="mt-3 space-y-2 text-sm">
          <li className="flex items-center justify-between">
            <span>Frontend (Next.js 15)</span>
            <StatusDot ok label="running" />
          </li>
          <li className="flex items-center justify-between">
            <span>Backend + Database (FastAPI + Supabase)</span>
            <StatusDot ok={status.ok} label={status.ok ? "connected" : "offline"} />
          </li>
        </ul>
        {!status.ok && (
          <p className="mt-3 text-xs text-muted-foreground">
            Start the backend with{" "}
            <code className="rounded bg-muted px-1">uvicorn app.main:app --reload --port 8000</code>{" "}
            and confirm your Supabase keys are set.
          </p>
        )}
      </div>

      <Link
        href="/dashboard"
        className="inline-flex w-fit items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Open compliance dashboard →
      </Link>
    </main>
  );
}

function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs font-medium">
      <span
        className={`h-2 w-2 rounded-full ${ok ? "bg-green-500" : "bg-destructive"}`}
        aria-hidden
      />
      {label}
    </span>
  );
}
