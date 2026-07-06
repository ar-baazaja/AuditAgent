-- =============================================================================
-- AuditAgent — Polar.sh billing linkage
-- Lets the webhook handler and future support tooling look up an org's Polar
-- customer/subscription without depending solely on webhook metadata.
-- Idempotent — safe to re-run.
-- =============================================================================
alter table public.organizations add column if not exists polar_customer_id text;
alter table public.organizations add column if not exists polar_subscription_id text;

create index if not exists idx_organizations_polar_subscription
  on public.organizations(polar_subscription_id);
