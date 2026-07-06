from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import asyncio
from typing import Any

from app.services import repository
from app.config import settings

# Attempt to load polar SDK
try:
    from polar_sdk import Polar
    polar = Polar(access_token=settings.polar_access_token)
except ImportError:
    polar = None

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Tiered plans (mock). Prices in USD/month.
PLANS = [
    {
        "tier": "free",
        "name": "Free",
        "price": 0,
        "features": ["1 framework", "Up to 10 controls", "Manual scans"],
        "limits": {"frameworks": 1, "scans_per_month": 20},
    },
    {
        "tier": "starter",
        "name": "Starter",
        "price": 199,
        "features": ["SOC 2 + HIPAA", "Automated evidence collection", "Email support"],
        "limits": {"frameworks": 2, "scans_per_month": 200},
    },
    {
        "tier": "growth",
        "name": "Growth",
        "price": 499,
        "features": ["Everything in Starter", "Gap analysis", "Auto-remediation tickets"],
        "limits": {"frameworks": 5, "scans_per_month": 2000},
    },
    {
        "tier": "enterprise",
        "name": "Enterprise",
        "price": None,  # "Contact us"
        "features": ["Unlimited frameworks", "SSO/SAML", "Dedicated CSM", "Custom controls"],
        "limits": {"frameworks": None, "scans_per_month": None},
    },
]


@router.get("/plans")
def get_plans():
    return PLANS


@router.get("/subscription")
def get_subscription(organization_id: str):
    org = repository.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    tier = org.get("billing_tier", "free")
    plan = next((p for p in PLANS if p["tier"] == tier), PLANS[0])
    return {
        "organization_id": organization_id,
        "current_tier": tier,
        "plan": plan,
        "status": "active",
        "provider": "polar" if settings.polar_access_token else "mock",
    }


@router.post("/checkout")
async def create_checkout(organization_id: str, tier: str):
    """Creates a real Polar checkout session if configured, else mock."""
    org = repository.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    if tier not in {p["tier"] for p in PLANS}:
        raise HTTPException(status_code=400, detail="unknown tier")

    if not polar:
        return {
            "checkout_url": f"https://mock-checkout.local/session?org={organization_id}&tier={tier}",
            "provider": "mock",
            "note": "Polar SDK not configured.",
        }

    try:
        # Fetch products to find the right one
        products_res = await polar.products.list_async()
        if not products_res.items:
            raise HTTPException(status_code=400, detail="No products found in Polar")
        
        # Use the first product by default, or match by name if we can
        product_id = products_res.items[0].id
        
        checkout = await polar.checkouts.create_async(
            request={
                "products": [product_id],
                "success_url": f"{settings.frontend_origin}/dashboard?checkout=success",
                "metadata": {"organization_id": organization_id, "tier": tier}
            }
        )
        return {
            "checkout_url": checkout.url,
            "provider": "polar"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def polar_webhook(request: Request):
    """Handle Polar webhooks (e.g. subscription.created)"""
    payload = await request.json()
    event_type = payload.get("type")
    
    if event_type in ("subscription.created", "subscription.updated"):
        data = payload.get("data", {})
        metadata = data.get("metadata", {})
        org_id = metadata.get("organization_id")
        tier = metadata.get("tier", "starter") # fallback
        
        if org_id:
            from app.db import get_supabase
            get_supabase().table("organizations").update({"billing_tier": tier}).eq("id", org_id).execute()
    
    return {"status": "received"}
