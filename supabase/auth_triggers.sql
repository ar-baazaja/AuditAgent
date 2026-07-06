-- =============================================================================
-- AuditAgent — Auth Triggers Migration
--
-- This script updates the `handle_new_user` function to automatically provision
-- an organization (workspace) for a user when they sign up, and adds them as
-- the 'owner' in the `organization_members` table.
-- =============================================================================

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  new_org_id uuid;
  user_full_name text;
  org_name text;
begin
  -- 1. Create the profile (mirrors auth.users)
  user_full_name := coalesce(new.raw_user_meta_data ->> 'full_name', split_part(new.email, '@', 1));
  
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, user_full_name)
  on conflict (id) do nothing;

  -- 2. Create a default organization for the new user
  org_name := user_full_name || '''s Workspace';
  
  insert into public.organizations (name, slug, billing_tier)
  values (org_name, generate_random_slug(org_name), 'free')
  returning id into new_org_id;

  -- 3. Add the user to the new organization as an 'owner'
  insert into public.organization_members (organization_id, user_id, role)
  values (new_org_id, new.id, 'owner');

  return new;
end $$;

-- Helper function to generate a unique slug
create or replace function public.generate_random_slug(base_name text)
returns text language plpgsql as $$
declare
  new_slug text;
  base_slug text;
  counter integer := 1;
begin
  -- Basic slugification (lowercase, replace spaces with hyphens, remove special chars)
  base_slug := lower(regexp_replace(base_name, '[^a-zA-Z0-9\s-]', '', 'g'));
  base_slug := regexp_replace(base_slug, '\s+', '-', 'g');
  new_slug := base_slug;
  
  -- Ensure uniqueness
  while exists(select 1 from public.organizations where slug = new_slug) loop
    new_slug := base_slug || '-' || counter;
    counter := counter + 1;
  end loop;
  
  return new_slug;
end $$;
