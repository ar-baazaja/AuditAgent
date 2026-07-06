-- =============================================================================
-- AuditAgent — Database Schema (Phase 1)
-- Target: Supabase (PostgreSQL 15+). Run this in the Supabase SQL Editor.
--
-- Design notes:
--   * Multi-tenant B2B: every business row is scoped to an organization_id.
--   * Auth is Supabase Auth (auth.users). We keep a mirrored `profiles` row.
--   * Row-Level Security (RLS) is ON for every tenant table. Users only ever
--     see rows for organizations they are a member of.
--   * pgvector is enabled now so Phase 4 (policy embeddings / semantic gap
--     analysis) needs no migration.
--   * Enums keep status/severity values consistent across the app.
-- =============================================================================

-- ----- Extensions -----------------------------------------------------------
create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "vector";      -- pgvector, for Phase 4 embeddings

-- ----- Enums ----------------------------------------------------------------
do $$ begin
  create type org_role         as enum ('owner', 'admin', 'auditor', 'viewer');
exception when duplicate_object then null; end $$;

do $$ begin
  create type control_status   as enum ('not_assessed', 'compliant', 'non_compliant', 'in_progress');
exception when duplicate_object then null; end $$;

do $$ begin
  create type evidence_result  as enum ('pass', 'fail', 'warning', 'info');
exception when duplicate_object then null; end $$;

do $$ begin
  create type evidence_source  as enum ('aws', 'github', 'manual', 'policy_doc');
exception when duplicate_object then null; end $$;

-- ----- Helper: auto-update updated_at ---------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- =============================================================================
-- ORGANIZATIONS  — one row per customer company (the tenant boundary)
-- =============================================================================
create table if not exists public.organizations (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  slug         text not null unique,
  -- Mocked billing now; maps cleanly to Polar.sh later (Phase 6).
  billing_tier text not null default 'free' check (billing_tier in ('free', 'starter', 'growth', 'enterprise')),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create trigger trg_org_updated before update on public.organizations
  for each row execute function public.set_updated_at();

-- =============================================================================
-- PROFILES  — app-level user record mirroring auth.users (1:1)
-- =============================================================================
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text not null,
  full_name   text,
  avatar_url  text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create trigger trg_profiles_updated before update on public.profiles
  for each row execute function public.set_updated_at();

-- Auto-create a profile whenever a new auth user signs up.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data ->> 'full_name')
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- =============================================================================
-- ORGANIZATION_MEMBERS  — join table (users <-> orgs) with roles
-- =============================================================================
create table if not exists public.organization_members (
  id              uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id         uuid not null references public.profiles(id) on delete cascade,
  role            org_role not null default 'viewer',
  created_at      timestamptz not null default now(),
  unique (organization_id, user_id)
);
create index if not exists idx_org_members_user on public.organization_members(user_id);
create index if not exists idx_org_members_org  on public.organization_members(organization_id);

-- SECURITY DEFINER helper: "is the current user a member of this org?"
-- Used by RLS policies below. Defined as a function to avoid recursive RLS.
create or replace function public.is_org_member(org uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from public.organization_members m
    where m.organization_id = org and m.user_id = auth.uid()
  );
$$;

-- =============================================================================
-- COMPLIANCE_FRAMEWORKS  — SOC 2, HIPAA, ... (GLOBAL, read-only catalog)
-- Not tenant-scoped: the framework definitions are shared reference data.
-- =============================================================================
create table if not exists public.compliance_frameworks (
  id          uuid primary key default gen_random_uuid(),
  key         text not null unique,          -- 'soc2', 'hipaa'
  name        text not null,                 -- 'SOC 2 Type II'
  version     text,                          -- '2017 TSC', etc.
  description text,
  created_at  timestamptz not null default now()
);

-- =============================================================================
-- CONTROLS  — individual requirements within a framework (GLOBAL catalog)
-- e.g. SOC2 CC6.1 "Logical access security". Tenant compliance is derived
-- from evidence_logs, not stored on the control itself.
-- =============================================================================
create table if not exists public.controls (
  id            uuid primary key default gen_random_uuid(),
  framework_id  uuid not null references public.compliance_frameworks(id) on delete cascade,
  code          text not null,               -- 'CC6.1'
  title         text not null,
  description   text,
  category      text,                        -- 'Access Control', 'Encryption', ...
  -- What automated check maps to this control (drives the agents in Phase 2).
  check_type    evidence_source,
  created_at    timestamptz not null default now(),
  unique (framework_id, code)
);
create index if not exists idx_controls_framework on public.controls(framework_id);

-- =============================================================================
-- EVIDENCE_LOGS  — TENANT-SCOPED. Every automated/manual check result.
-- This is what the multi-agent backend writes and the dashboard reads.
-- =============================================================================
create table if not exists public.evidence_logs (
  id              uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  control_id      uuid not null references public.controls(id) on delete restrict,
  source          evidence_source not null,
  result          evidence_result not null,
  status          control_status  not null default 'not_assessed',
  summary         text,                       -- human-readable finding
  raw_evidence    jsonb not null default '{}'::jsonb,  -- captured infra config
  -- Optional embedding for semantic search / gap analysis (Phase 4).
  embedding       vector(768),
  collected_by    text,                       -- 'agent:evidence-collector' | user id
  collected_at    timestamptz not null default now(),
  created_at      timestamptz not null default now()
);
create index if not exists idx_evidence_org      on public.evidence_logs(organization_id);
create index if not exists idx_evidence_control  on public.evidence_logs(control_id);
create index if not exists idx_evidence_status   on public.evidence_logs(organization_id, status);

-- =============================================================================
-- REMEDIATION_TICKETS  — TENANT-SCOPED. Auto-generated mock Jira/Linear tickets
-- created when a control fails (Phase 5).
-- =============================================================================
do $$ begin
  create type ticket_severity as enum ('low', 'medium', 'high', 'critical');
exception when duplicate_object then null; end $$;

do $$ begin
  create type ticket_status   as enum ('open', 'in_progress', 'closed');
exception when duplicate_object then null; end $$;

create table if not exists public.remediation_tickets (
  id              uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  control_id      uuid not null references public.controls(id) on delete cascade,
  provider        text not null default 'linear' check (provider in ('jira', 'linear')),
  provider_ref    text,                        -- fake ticket key e.g. 'LIN-1042'
  title           text not null,
  description     text,
  suggested_fix   text,
  severity        ticket_severity not null default 'medium',
  status          ticket_status   not null default 'open',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists idx_tickets_org on public.remediation_tickets(organization_id);
create trigger trg_tickets_updated before update on public.remediation_tickets
  for each row execute function public.set_updated_at();

-- =============================================================================
-- ROW-LEVEL SECURITY
-- =============================================================================
alter table public.organizations         enable row level security;
alter table public.profiles               enable row level security;
alter table public.organization_members   enable row level security;
alter table public.evidence_logs          enable row level security;
alter table public.remediation_tickets    enable row level security;
-- Frameworks & controls are a public read-only catalog (RLS with open SELECT).
alter table public.compliance_frameworks  enable row level security;
alter table public.controls               enable row level security;

-- profiles: a user can see/update only their own profile.
drop policy if exists "own profile read"   on public.profiles;
create policy "own profile read"   on public.profiles for select using (id = auth.uid());
drop policy if exists "own profile update" on public.profiles;
create policy "own profile update" on public.profiles for update using (id = auth.uid());

-- organizations: members can read; owners/admins can update.
drop policy if exists "member reads org" on public.organizations;
create policy "member reads org" on public.organizations
  for select using (public.is_org_member(id));

-- organization_members: a user sees membership rows for orgs they belong to.
drop policy if exists "read own memberships" on public.organization_members;
create policy "read own memberships" on public.organization_members
  for select using (user_id = auth.uid() or public.is_org_member(organization_id));

-- evidence_logs: full access scoped to the user's organizations.
drop policy if exists "member reads evidence" on public.evidence_logs;
create policy "member reads evidence" on public.evidence_logs
  for select using (public.is_org_member(organization_id));
drop policy if exists "member writes evidence" on public.evidence_logs;
create policy "member writes evidence" on public.evidence_logs
  for insert with check (public.is_org_member(organization_id));

-- remediation_tickets: scoped to the user's organizations.
drop policy if exists "member reads tickets" on public.remediation_tickets;
create policy "member reads tickets" on public.remediation_tickets
  for select using (public.is_org_member(organization_id));

-- Catalog tables: readable by any authenticated user.
drop policy if exists "read frameworks" on public.compliance_frameworks;
create policy "read frameworks" on public.compliance_frameworks
  for select using (auth.role() = 'authenticated');
drop policy if exists "read controls" on public.controls;
create policy "read controls" on public.controls
  for select using (auth.role() = 'authenticated');

-- NOTE: the FastAPI backend uses the service_role key, which bypasses RLS,
-- so agents can write evidence_logs for any org they are orchestrating.
