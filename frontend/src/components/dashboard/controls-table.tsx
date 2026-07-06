import type { ControlRow } from "@/lib/api";
import { statusBadge } from "@/lib/format";
import { Badge } from "@/components/ui/badge";

export function ControlsTable({ controls }: { controls: ControlRow[] }) {
  if (controls.length === 0) {
    return (
      <p className="rounded-lg border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
        No controls found. Run the database seed (supabase/seed.sql).
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Framework</th>
            <th className="px-4 py-3 font-medium">Control</th>
            <th className="px-4 py-3 font-medium">Category</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Latest finding</th>
          </tr>
        </thead>
        <tbody>
          {controls.map((c) => {
            const badge = statusBadge(c.status);
            return (
              <tr key={c.control_id} className="border-b last:border-0 hover:bg-muted/30">
                <td className="px-4 py-3">
                  <span className="uppercase text-xs font-medium text-muted-foreground">
                    {c.framework_key}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="font-medium">{c.code}</div>
                  <div className="text-xs text-muted-foreground">{c.title}</div>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{c.category}</td>
                <td className="px-4 py-3">
                  <Badge variant={badge.variant}>{badge.label}</Badge>
                </td>
                <td className="max-w-xs px-4 py-3 text-xs text-muted-foreground">
                  {c.summary ?? "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
