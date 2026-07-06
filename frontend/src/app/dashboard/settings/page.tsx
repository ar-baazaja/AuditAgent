"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, ExternalLink, Github, Loader2 } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { api, type IntegrationSettings } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

/**
 * Lets each customer connect THEIR OWN GitHub App installation / AWS IAM
 * role. Saved values are read by the backend connectors
 * (app/connectors/github.py, aws.py) on every scan — no code change needed
 * per customer, just this row in the `integrations` table.
 */
export default function SettingsPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [githubId, setGithubId] = useState("");
  const [awsArn, setAwsArn] = useState("");
  const [awsRegion, setAwsRegion] = useState("us-east-1");
  const [loading, setLoading] = useState(true);
  const [savingGithub, setSavingGithub] = useState(false);
  const [savingAws, setSavingAws] = useState(false);
  const [savedGithub, setSavedGithub] = useState(false);
  const [savedAws, setSavedAws] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const supabase = createClient();
        const {
          data: { user },
        } = await supabase.auth.getUser();
        if (!user) {
          window.location.href = "/login";
          return;
        }
        const { data: members } = await supabase
          .from("organization_members")
          .select("organization_id")
          .eq("user_id", user.id)
          .limit(1);
        const currentOrgId = members?.[0]?.organization_id;
        if (!currentOrgId) {
          setError("You don't belong to any organization.");
          return;
        }
        setOrgId(currentOrgId);

        const settings = await api.getSettings(currentOrgId);
        setGithubId(settings.github_installation_id ?? "");
        setAwsArn(settings.aws_role_arn ?? "");
        setAwsRegion(settings.aws_region ?? "us-east-1");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load settings");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function saveGithub() {
    if (!orgId) return;
    setSavingGithub(true);
    setError(null);
    try {
      await api.updateSettings({
        organization_id: orgId,
        github_installation_id: githubId || null,
        aws_role_arn: awsArn || null,
        aws_region: awsRegion,
      });
      setSavedGithub(true);
      setTimeout(() => setSavedGithub(false), 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSavingGithub(false);
    }
  }

  async function saveAws() {
    if (!orgId) return;
    setSavingAws(true);
    setError(null);
    try {
      await api.updateSettings({
        organization_id: orgId,
        github_installation_id: githubId || null,
        aws_role_arn: awsArn || null,
        aws_region: awsRegion,
      });
      setSavedAws(true);
      setTimeout(() => setSavedAws(false), 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSavingAws(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading settings…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-2xl font-bold tracking-tight">Integration Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Connect your own AWS account and GitHub organization so compliance scans
        read your real infrastructure instead of sample data.
      </p>

      {error && (
        <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mt-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Github className="h-4 w-4" /> GitHub Integration
            </CardTitle>
            <CardDescription>
              Install the AuditAgent GitHub App on your organization, then paste the
              installation ID below.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <a
              href="https://github.com/apps"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              Install the GitHub App <ExternalLink className="h-3.5 w-3.5" />
            </a>
            <div>
              <label className="mb-1 block text-sm font-medium">
                GitHub App Installation ID
              </label>
              <input
                value={githubId}
                onChange={(e) => setGithubId(e.target.value)}
                placeholder="e.g. 12345678"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
            </div>
            <Button onClick={saveGithub} disabled={savingGithub}>
              {savingGithub ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : savedGithub ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : null}
              {savedGithub ? "Saved" : "Save GitHub settings"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">AWS Integration</CardTitle>
            <CardDescription>
              Create an IAM role that trusts AuditAgent (with an ExternalId) and
              paste its ARN below.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">IAM Role ARN</label>
              <input
                value={awsArn}
                onChange={(e) => setAwsArn(e.target.value)}
                placeholder="arn:aws:iam::123456789012:role/AuditAgentScanner"
                className="w-full rounded-md border bg-background px-3 py-2 font-mono text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">AWS Region</label>
              <input
                value={awsRegion}
                onChange={(e) => setAwsRegion(e.target.value)}
                placeholder="us-east-1"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
            </div>
            <Button onClick={saveAws} disabled={savingAws}>
              {savingAws ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : savedAws ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : null}
              {savedAws ? "Saved" : "Save AWS settings"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
