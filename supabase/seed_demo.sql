-- =============================================================================
-- AuditAgent — Demo Organization (optional, for local development)
-- Run AFTER schema.sql + seed.sql. Lets you exercise the full stack (scans,
-- scores, tickets) WITHOUT wiring up auth first. Safe to re-run.
--
-- The fixed UUID below is what you put in the frontend's
-- NEXT_PUBLIC_DEMO_ORG_ID so the dashboard has an org to display.
-- =============================================================================
insert into public.organizations (id, name, slug, billing_tier)
values ('00000000-0000-0000-0000-0000000000de', 'Acme Health Inc.', 'acme-health', 'growth')
on conflict (id) do update set name = excluded.name, billing_tier = excluded.billing_tier;
