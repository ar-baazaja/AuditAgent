/**
 * Typed client for the FastAPI backend.
 * Runs in the browser (dashboard is interactive), so it only uses the public
 * NEXT_PUBLIC_* env vars — never a secret.
 */
const BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
export const DEMO_ORG_ID = process.env.NEXT_PUBLIC_DEMO_ORG_ID ?? "";

// ---- Types (mirror backend schemas) --------------------------------------
export type ControlStatus =
  | "not_assessed"
  | "compliant"
  | "non_compliant"
  | "in_progress";

export interface FrameworkScore {
  framework_key: string;
  framework_name: string;
  total_controls: number;
  assessed: number;
  compliant: number;
  non_compliant: number;
  score: number;
}

export interface ComplianceOverview {
  organization_id: string;
  overall_score: number;
  frameworks: FrameworkScore[];
}

export interface ControlRow {
  framework_key: string;
  framework_name: string;
  control_id: string;
  code: string;
  title: string;
  category: string;
  status: ControlStatus;
  result: string | null;
  summary: string | null;
  collected_at: string | null;
}

export interface Ticket {
  id: string;
  provider: string;
  provider_ref: string;
  title: string;
  description: string;
  suggested_fix: string;
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  created_at: string;
}

export interface ScanResponse {
  frameworks_scanned: string[];
  controls_evaluated: number;
  passed: number;
  failed: number;
}

export interface Subscription {
  organization_id: string;
  current_tier: string;
  plan: { name: string; price: number | null; features: string[] };
  status: string;
}

export interface IntegrationSettings {
  organization_id: string;
  github_installation_id: string | null;
  aws_role_arn: string | null;
  aws_region: string | null;
}

import { createClient } from "@/lib/supabase/client";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  
  const headers: Record<string, string> = { 
    "Content-Type": "application/json", 
    ...(init?.headers as Record<string, string> ?? {}) 
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  agentStatus: () =>
    request<{ evaluation_engine: string; llm_available: boolean }>(
      "/api/v1/agents/status",
    ),
  overview: (orgId: string) =>
    request<ComplianceOverview>(
      `/api/v1/compliance/overview?organization_id=${orgId}`,
    ),
  controls: (orgId: string) =>
    request<ControlRow[]>(`/api/v1/compliance/controls?organization_id=${orgId}`),
  tickets: (orgId: string) =>
    request<Ticket[]>(`/api/v1/remediation/tickets?organization_id=${orgId}`),
  subscription: (orgId: string) =>
    request<Subscription>(`/api/v1/billing/subscription?organization_id=${orgId}`),
  runScan: (orgId: string, frameworkKey?: string) =>
    request<ScanResponse>("/api/v1/agents/scan", {
      method: "POST",
      body: JSON.stringify({ organization_id: orgId, framework_key: frameworkKey ?? null }),
    }),
  gapAnalysis: (orgId: string, frameworkKey: string) =>
    request<{ controls_with_gaps: number; findings: unknown[] }>(
      "/api/v1/gap-analysis",
      {
        method: "POST",
        body: JSON.stringify({ organization_id: orgId, framework_key: frameworkKey }),
      },
    ),
  createCheckout: (orgId: string, tier: string) =>
    request<{ checkout_url: string; provider: string }>(
      `/api/v1/billing/checkout?organization_id=${orgId}&tier=${tier}`,
      { method: "POST" }
    ),
  getSettings: (orgId: string) =>
    request<IntegrationSettings>(`/api/v1/settings?organization_id=${orgId}`),
  updateSettings: (payload: IntegrationSettings) =>
    request<IntegrationSettings>("/api/v1/settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
};
