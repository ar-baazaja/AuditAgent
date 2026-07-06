"""AuditAgent FastAPI entrypoint.

Wires together every phase:
  * /health, /health/db            — liveness / readiness
  * /api/v1/frameworks             — compliance catalog
  * /api/v1/organizations          — tenants
  * /api/v1/agents/*               — Phase 2: multi-agent scans
  * /api/v1/compliance/*           — Phase 3: posture, scores, evidence
  * /api/v1/gap-analysis           — Phase 4: policy vs infra gaps
  * /api/v1/remediation/*          — Phase 5: auto-remediation tickets
  * /api/v1/billing/*              — Phase 6: mock (Polar.sh-ready) billing
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import get_supabase
from app.routers import (
    agents,
    billing,
    compliance,
    gap_analysis,
    organizations,
    remediation,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_supabase()  # warm the cached client at startup
    yield


app = FastAPI(
    title="AuditAgent API",
    version="1.0.0",
    description="Multi-agent compliance monitoring & audit automation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "AuditAgent API", "version": app.version, "env": settings.app_env}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        get_supabase().table("compliance_frameworks").select("id").limit(1).execute()
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"database unreachable: {exc}")


@app.get("/api/v1/frameworks")
def list_frameworks():
    supabase = get_supabase()
    frameworks = supabase.table("compliance_frameworks").select("*").execute().data
    controls = supabase.table("controls").select("*").execute().data
    by_framework: dict[str, list] = {}
    for control in controls:
        by_framework.setdefault(control["framework_id"], []).append(control)
    return [{**fw, "controls": by_framework.get(fw["id"], [])} for fw in frameworks]


# Feature routers.
app.include_router(organizations.router)
app.include_router(agents.router)
app.include_router(compliance.router)
app.include_router(gap_analysis.router)
app.include_router(remediation.router)
app.include_router(billing.router)
