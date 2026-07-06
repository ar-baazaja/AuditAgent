"""Billing endpoints — real Polar.sh checkout + webhook (Phase 6).

Plans are defined here (source of truth for the app); each paid tier maps to
a real Polar Product ID via env vars so `/checkout` always sells the product
the user actually clicked, not "whatever Polar returns first."

The webhook is signature-verified (Standard Webhooks / Svix, which Polar
uses) — without this, anyone who finds the endpoint could POST a fake
"subscription.created" and grant themselves any tier for free.
"""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user, verify_organization_access
from app.config import settings
from app.db import get_supabase
from app.services import repository

try:
    from polar_sdk import Polar

    polar = Polar(access_token=settings.polar_access_token, server=settings.polar_server) \
        if settings.polar_access_token else None
except ImportError:  # pragma: no cover - dependency missing locally
    polar = None

try:
    from standardwebhooks.webhooks import Webhook as StandardWebhook
except ImportError:  # pragma: no cover
    StandardWebhook = None

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Tiered plans. `polar_product_id` is populated from env so each tier checks
# out the correct Polar product — never "the first product in the account."
PLANS = [
    {
        "tier": "free",
        "name": "Free",
        "price": 0,
        "features": ["1 framework", "Up to 10 controls", "Manual scans"],
        "limits": {"frameworks": 1, "scans_per_month": 20},
        "polar_product_id": None,
    },
    {
        "tier": "starter",
        "name": "Starter",
        "price": 199,
        "features": ["SOC 2 + HIPAA", "Automated evidence collection", "Email support"],
        "limits": {"frameworks": 2, "scans_per_month": 200},
        "polar_product_id": settings.polar_product_starter_id or None,
    },
    {
        "tier": "growth",
        "name": "Growth",
        "price": 499,
        "features": ["Everything in Starter", "Gap analysis", "Auto-remediation tickets"],
        "limits": {"frameworks": 5, "scans_per_month": 2000},
        "polar_product_id": settings.polar_product_growth_id or None,
    },
    {
        "tier": "enterprise",
        "name": "Enterprise",
        "price": None,  # "Contact us" — no self-serve checkout
        "features": ["Unlimited frameworks", "SSO/SAML", "Dedicated CSM", "Custom controls"],
        "limits": {"frameworks": None, "scans_per_month": None},
        "polar_product_id": None,
    },
]

# Reverse lookup used by the webhook: Polar product id -> our tier key.
_PRODUCT_ID_TO_TIER = {
    p["polar_product_id"]: p["tier"] for p in PLANS if p["polar_product_id"]
}


def _plan_for(tier: str) -> dict:
    return next((p for p in PLANS if p["tier"] == tier), PLANS[0])


@router.get("/plans")
def get_plans():
    # Don't leak Polar product IDs to the client — internal wiring only.
    return [{k: v for k, v in p.items() if k != "polar_product_id"} for p in PLANS]


@router.get("/subscription")
def get_subscription(organization_id: str = Depends(verify_organization_access)):
    org = repository.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    tier = org.get("billing_tier", "free")
    plan = _plan_for(tier)
    return {
        "organization_id": organization_id,
        "current_tier": tier,
        "plan": {k: v for k, v in plan.items() if k != "polar_product_id"},
        "status": "active",
        "provider": "polar" if polar else "mock",
    }


@router.post("/checkout")
async def create_checkout(organization_id: str, tier: str, user_id: str = Depends(get_current_user)):
    """Create a Polar checkout session for the requested tier."""
    verify_organization_access(organization_id, user_id)
    org = repository.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")

    plan = _plan_for(tier)
    if plan["tier"] != tier:
        raise HTTPException(status_code=400, detail="unknown tier")
    if plan["price"] is None:
        raise HTTPException(status_code=400, detail="this tier has no self-serve checkout — contact sales")

    if not polar:
        return {
            "checkout_url": f"https://mock-checkout.local/session?org={organization_id}&tier={tier}",
            "provider": "mock",
            "note": "Polar is not configured (missing POLAR_ACCESS_TOKEN).",
        }

    product_id = plan["polar_product_id"]
    if not product_id:
        raise HTTPException(
            status_code=500,
            detail=f"No Polar product configured for tier '{tier}'. "
            f"Set POLAR_PRODUCT_{tier.upper()}_ID.",
        )

    try:
        checkout = await polar.checkouts.create_async(
            request={
                "products": [product_id],
                "success_url": f"{settings.frontend_origin}/dashboard?checkout=success",
                "metadata": {"organization_id": organization_id, "tier": tier},
            }
        )
        return {"checkout_url": checkout.url, "provider": "polar"}
    except Exception as e:  # noqa: BLE001 — surface the Polar error to the caller
        raise HTTPException(status_code=502, detail=f"Polar checkout failed: {e}")


@router.post("/webhook")
async def polar_webhook(request: Request):
    """Handle Polar subscription lifecycle events.

    Verifies the Standard Webhooks signature Polar sends before trusting the
    payload — otherwise anyone could POST a forged "subscription.created" and
    upgrade any organization for free.
    """
    body = await request.body()

    if not settings.polar_webhook_secret or not StandardWebhook:
        # Refuse rather than silently trust an unverifiable payload.
        raise HTTPException(status_code=503, detail="webhook verification not configured")

    try:
        wh = StandardWebhook(settings.polar_webhook_secret)
        payload = wh.verify(body, dict(request.headers))
    except Exception:
        raise HTTPException(status_code=401, detail="invalid webhook signature")

    event_type = payload.get("type")
    data = payload.get("data", {})
    metadata = data.get("metadata", {}) or {}
    org_id = metadata.get("organization_id")

    # Prefer resolving the tier from the actual Polar product purchased —
    # metadata is only present on events tied to our checkout, product id
    # is present on every subscription event Polar sends.
    product_id = (data.get("product") or {}).get("id") or data.get("product_id")
    tier = _PRODUCT_ID_TO_TIER.get(product_id) or metadata.get("tier")

    customer_id = (data.get("customer") or {}).get("id") or data.get("customer_id")
    subscription_id = data.get("id")

    if event_type in ("subscription.created", "subscription.updated", "subscription.active"):
        if org_id and tier:
            get_supabase().table("organizations").update(
                {
                    "billing_tier": tier,
                    "polar_customer_id": customer_id,
                    "polar_subscription_id": subscription_id,
                }
            ).eq("id", org_id).execute()
    elif event_type in ("subscription.canceled", "subscription.revoked"):
        if org_id:
            get_supabase().table("organizations").update({"billing_tier": "free"}).eq(
                "id", org_id
            ).execute()

    return {"status": "received"}
