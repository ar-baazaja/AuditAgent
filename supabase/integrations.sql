-- Create the integrations table to map organizations to their connected cloud providers
create table public.integrations (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid references public.organizations(id) on delete cascade not null,
  aws_role_arn text,
  github_installation_id text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  unique (organization_id)
);

-- Enable RLS
alter table public.integrations enable row level security;

-- Only organization members can read their integrations
create policy "Users can view their organization's integrations"
  on public.integrations for select
  using (
    exists (
      select 1 from public.organization_members
      where organization_id = integrations.organization_id
      and user_id = auth.uid()
    )
  );

-- Backend service role needs full access
create policy "Service role has full access to integrations"
  on public.integrations for all
  using (true)
  with check (true);
