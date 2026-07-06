import { useState } from "react";
import { Check, ExternalLink, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Subscription } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function BillingCard({ subscription }: { subscription: Subscription }) {
  const { plan, current_tier, status, organization_id } = subscription;
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      // In a real app, you'd choose the tier to upgrade to. Here we upgrade to 'starter'
      const targetTier = current_tier === "free" ? "starter" : "growth";
      
      const res = await api(`/api/v1/billing/checkout?organization_id=${organization_id}&tier=${targetTier}`, {
        method: "POST"
      });
      
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      } else {
        alert("Could not generate checkout session.");
      }
    } catch (err) {
      console.error(err);
      alert("Failed to initiate checkout.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{plan.name}</CardTitle>
          <Badge variant="success">{status}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {plan.price === null ? "Custom pricing" : `$${plan.price}/mo`} ·{" "}
          <span className="uppercase">{current_tier}</span>
        </p>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm mb-6">
          {plan.features.map((f) => (
            <li key={f} className="flex items-center gap-2">
              <Check className="h-4 w-4 text-green-500" />
              {f}
            </li>
          ))}
        </ul>
        
        {plan.price !== null && (
          <Button 
            className="w-full" 
            onClick={handleUpgrade} 
            disabled={loading}
          >
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ExternalLink className="mr-2 h-4 w-4" />}
            Upgrade Plan
          </Button>
        )}
        
        <p className="mt-4 text-xs text-muted-foreground">
          Payments powered by Polar.sh.
        </p>
      </CardContent>
    </Card>
  );
}
