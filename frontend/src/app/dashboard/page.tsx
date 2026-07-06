"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Loader2, RefreshCw, ShieldCheck } from "lucide-react";

import {
  api,
  DEMO_ORG_ID,
  type ComplianceOverview,
  type ControlRow,
  type Subscription,
  type Ticket,
} from "@/lib/api";
import { scoreColor } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScoreDonut } from "@/components/dashboard/score-donut";
import { ControlsTable } from "@/components/dashboard/controls-table";
import { TicketsList } from "@/components/dashboard/tickets-list";
import { BillingCard } from "@/components/dashboard/billing-card";

export default function DashboardPage() {
  const orgId = DEMO_ORG_ID;
  const [overview, setOverview] = useState<ComplianceOverview | null>(null);
  const [controls, setControls] = useState<ControlRow[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [engine, setEngine] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!orgId) {
      setError("NEXT_PUBLIC_DEMO_ORG_ID is not set. See .env.local.example.");
      setLoading(false);
      return;
    }
    try {
      setError(null);
      const [ov, ctrls, tks, sub, status] = await Promise.all([
        api.overview(orgId),
        api.controls(orgId),
        api.tickets(orgId),
        api.subscription(orgId),
        api.agentStatus(),
      ]);
      setOverview(ov);
      setControls(ctrls);
      setTickets(tks);
      setSubscription(sub);
      setEngine(status.evaluation_engine);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    load();
  }, [load]);

  async function runScan() {
    setScanning(true);
    setError(null);
    try {
      await api.runScan(orgId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading dashboard…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6" />
            <h1 className="text-2xl font-bold tracking-tight">Compliance Posture</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            SOC 2 &amp; HIPAA · evaluation engine:{" "}
            <span className="font-medium">{engine || "unknown"}</span>
          </p>
        </div>
        <Button onClick={runScan} disabled={scanning}>
          {scanning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {scanning ? "Running agents…" : "Run compliance scan"}
        </Button>
      </div>

      {error && (
        <div className="mt-6 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {overview && (
        <>
          {/* Score summary */}
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <Card className="md:col-span-1">
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">
                  Overall score
                </CardTitle>
              </CardHeader>
              <CardContent className="flex justify-center">
                <ScoreDonut score={overview.overall_score} />
              </CardContent>
            </Card>

            <div className="grid gap-4 md:col-span-2">
              {overview.frameworks.map((fw) => (
                <Card key={fw.framework_key}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{fw.framework_name}</CardTitle>
                      <span className="text-2xl font-bold">{fw.score}%</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Progress
                      value={fw.score}
                      indicatorClassName={scoreColor(fw.score)}
                    />
                    <p className="mt-2 text-xs text-muted-foreground">
                      {fw.compliant} compliant · {fw.non_compliant} failing ·{" "}
                      {fw.assessed}/{fw.total_controls} controls assessed
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {overview.frameworks.every((f) => f.assessed === 0) && (
            <div className="mt-6 rounded-lg border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
              No evidence collected yet. Click{" "}
              <span className="font-medium">Run compliance scan</span> to launch the
              multi-agent pipeline.
            </div>
          )}

          {/* Controls */}
          <section className="mt-10">
            <h2 className="mb-3 text-lg font-semibold">Controls</h2>
            <ControlsTable controls={controls} />
          </section>

          {/* Tickets + Billing */}
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            <section>
              <h2 className="mb-3 text-lg font-semibold">
                Remediation tickets{" "}
                <span className="text-sm font-normal text-muted-foreground">
                  ({tickets.length})
                </span>
              </h2>
              <TicketsList tickets={tickets} />
            </section>
            <section>
              <h2 className="mb-3 text-lg font-semibold">Plan</h2>
              {subscription && <BillingCard subscription={subscription} />}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
