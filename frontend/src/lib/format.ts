import type { ControlStatus } from "@/lib/api";

/** Map a control status to a Badge variant + label. */
export function statusBadge(status: ControlStatus): {
  variant: "success" | "destructive" | "warning" | "secondary";
  label: string;
} {
  switch (status) {
    case "compliant":
      return { variant: "success", label: "Compliant" };
    case "non_compliant":
      return { variant: "destructive", label: "Non-compliant" };
    case "in_progress":
      return { variant: "warning", label: "In progress" };
    default:
      return { variant: "secondary", label: "Not assessed" };
  }
}

export function severityBadge(severity: string): {
  variant: "destructive" | "warning" | "secondary";
  label: string;
} {
  if (severity === "critical" || severity === "high")
    return { variant: "destructive", label: severity };
  if (severity === "medium") return { variant: "warning", label: severity };
  return { variant: "secondary", label: severity };
}

/** Tailwind indicator color for a 0-100 score. */
export function scoreColor(score: number): string {
  if (score >= 85) return "bg-green-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}
