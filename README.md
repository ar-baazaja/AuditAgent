# AuditAgent

Multi-Agent AI Compliance Monitoring & Audit Automation Platform (SOC 2 + HIPAA) for mid-market B2B.

This is a monorepo with three parts:

```
AuditAgent/
├── frontend/      # Next.js 15 (App Router) + React 19 + Tailwind v4 + shadcn/ui
├── backend/       # Python FastAPI — multi-agent orchestration (LangChain, Phase 2)
└── supabase/      # PostgreSQL schema + seed data (pgvector enabled)
```

Everything runs locally or on 100% free tiers. See **Setup** below.

---

## Architecture (why it's split this way)

| Concern | Owner | Reason |
|---|---|---|
| Auth, standard CRUD, dashboard SSR | Next.js API routes + Supabase | Cheap, colocated with UI, RLS-secured |
| Multi-agent AI orchestration | Python FastAPI | LangChain/LlamaIndex ecosystem is Python-first |
| Data + vectors + auth | Supabase (Postgres + pgvector) | Single free-tier datastore, row-level security |
| LLM | Gemini 1.5/2.0 Flash (free tier) | No cost during dev; swappable via env |

The two backends share **one** Supabase database. Next.js talks to it via `@supabase/ssr`
(user-scoped, RLS-enforced). FastAPI talks to it via the `service_role` key (trusted
server, bypasses RLS) only for agent-written evidence.

---

## Build phases — all implemented ✅

- **Phase 1:** Project init + database schema (multi-tenant, RLS, pgvector).
- **Phase 2:** Multi-agent FastAPI backend — Agent A (evidence collector) pulls mock AWS/GitHub config, Agent B (evaluator) judges each control via Gemini Flash (heuristic fallback), orchestrator persists evidence.
- **Phase 3:** Interactive dashboard — overall + per-framework scores, controls table, live "Run scan".
- **Phase 4:** LLM gap analysis — company policy Markdown vs. actual infra settings.
- **Phase 5:** Auto-remediation — failing controls auto-generate mock Jira/Linear tickets with concrete fixes.
- **Phase 6:** Mock billing (tiered B2B plans, Polar.sh-ready).

### How the multi-agent scan works

```
POST /api/v1/agents/scan
      │
      ▼
ComplianceOrchestrator ── for each control in framework ──┐
      │                                                    │
      ├─ Agent A: EvidenceCollector → mock AWS/GitHub connector → raw config
      ├─ Agent B: ControlEvaluator  → Gemini Flash (or heuristic) → pass/fail + summary
      ├─ persist → evidence_logs
      └─ if non_compliant → Phase 5 → remediation_tickets (mock Jira/Linear)
```

Scores are always **computed from evidence at read time** (`services/scoring.py`) — never stored.

### LLM is optional

The evaluator and gap analyzer prefer the LLM but fall back to a deterministic
rule engine when `GOOGLE_API_KEY` is absent — so the platform runs fully offline.
Check `GET /api/v1/agents/status` to see which engine is active.

---

## Setup

Prerequisites: **Node 20+**, **Python 3.11+**, a free **Supabase** project, a free **Google AI Studio** key (used in Phase 2).

### 1. Database
1. Create a project at https://supabase.com (free tier).
2. Open the **SQL Editor** and run, in order:
   1. `supabase/schema.sql` — tables, enums, RLS, pgvector.
   2. `supabase/seed.sql` — SOC 2 + HIPAA frameworks and controls.
   3. `supabase/seed_demo.sql` — a demo organization so you can use the
      dashboard immediately without setting up auth first.

### 2. Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # then fill in values (see "API keys" below)
npm run dev                          # http://localhost:3000
```

### 3. Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # then fill in values
uvicorn app.main:app --reload --port 8000   # http://localhost:8000/health
```

---

## Where to put API keys

Nothing is hardcoded — every secret is read from environment files that are **git-ignored**.

### `frontend/.env.local`
| Variable | Where to get it |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Project Settings → API → `anon` `public` key |
| `NEXT_PUBLIC_BACKEND_URL` | Your FastAPI URL — `http://localhost:8000` in dev |
| `NEXT_PUBLIC_DEMO_ORG_ID` | The fixed UUID from `seed_demo.sql` (already pre-filled in the example) |

### `backend/.env`
| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Same Project URL as above |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API → `service_role` key (**secret — server only**) |
| `GOOGLE_API_KEY` | https://aistudio.google.com/app/apikey (free) — used in Phase 2 |
| `FRONTEND_ORIGIN` | `http://localhost:3000` in dev (CORS allow-list) |

> ⚠️ The `service_role` key bypasses row-level security. It lives **only** in `backend/.env`
> and is never exposed to the browser.

---

## First run (end-to-end in 60 seconds)

1. Start the backend (`uvicorn ... --port 8000`) and frontend (`npm run dev`).
2. Open **http://localhost:3000** → status page shows both services green.
3. Click **Open compliance dashboard** → http://localhost:3000/dashboard.
4. Click **Run compliance scan**. The multi-agent pipeline collects mock evidence,
   evaluates every SOC 2 + HIPAA control, and writes results.
5. Watch the scores populate, failing controls appear in the table, and
   remediation tickets (with code fixes) get auto-generated.

Without a `GOOGLE_API_KEY` the scan still works using the heuristic engine.
Add the key to enable real LLM evaluation and gap analysis.

## API reference (FastAPI, interactive docs at `/docs`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health/db` | Readiness (Supabase reachable) |
| GET | `/api/v1/frameworks` | Framework + control catalog |
| GET | `/api/v1/organizations` | List tenants |
| GET | `/api/v1/agents/status` | Active evaluation engine (llm/heuristic) |
| POST | `/api/v1/agents/scan` | Run the multi-agent compliance scan |
| GET | `/api/v1/compliance/overview` | Scores per framework + overall |
| GET | `/api/v1/compliance/controls` | Every control + latest status |
| GET | `/api/v1/compliance/evidence` | Recent evidence logs |
| POST | `/api/v1/gap-analysis` | Policy-vs-infra gap findings |
| GET/POST | `/api/v1/remediation/tickets` | List / create remediation tickets |
| GET | `/api/v1/billing/plans` · `/subscription` | Mock tiered billing |

## Going to production later (swap points)

| Mock | Replace with |
|---|---|
| `app/mocks/connectors.py` | Real `boto3` (AWS) + GitHub REST calls |
| `app/mocks/policies/*.md` | Per-org uploaded policies embedded into pgvector |
| `app/services/remediation.py` `_make_provider_ref` | Real Jira/Linear API create-issue |
| `app/routers/billing.py` PLANS | Polar.sh products + checkout sessions |
| `NEXT_PUBLIC_DEMO_ORG_ID` | Real org resolved from the signed-in user (Supabase Auth + `organization_members`) |
