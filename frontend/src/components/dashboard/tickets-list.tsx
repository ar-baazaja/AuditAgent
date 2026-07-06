"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import type { Ticket } from "@/lib/api";
import { severityBadge } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export function TicketsList({ tickets }: { tickets: Ticket[] }) {
  if (tickets.length === 0) {
    return (
      <p className="rounded-lg border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
        No open tickets. Failing controls auto-generate remediation tickets during a scan.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {tickets.map((t) => (
        <TicketItem key={t.id} ticket={t} />
      ))}
    </div>
  );
}

function TicketItem({ ticket }: { ticket: Ticket }) {
  const [open, setOpen] = useState(false);
  const sev = severityBadge(ticket.severity);
  return (
    <Card>
      <CardContent className="p-4">
        <button
          className="flex w-full items-start justify-between gap-3 text-left"
          onClick={() => setOpen((o) => !o)}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                {ticket.provider_ref}
              </span>
              <Badge variant={sev.variant}>{sev.label}</Badge>
            </div>
            <p className="mt-1 truncate text-sm font-medium">{ticket.title}</p>
          </div>
          {open ? (
            <ChevronDown className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
          )}
        </button>
        {open && (
          <div className="mt-3 space-y-3 border-t pt-3">
            <p className="text-sm text-muted-foreground">{ticket.description}</p>
            <div>
              <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">
                Suggested fix
              </p>
              <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
                {ticket.suggested_fix}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
