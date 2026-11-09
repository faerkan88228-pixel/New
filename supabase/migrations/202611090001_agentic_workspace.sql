-- Agentic Workspace repository overlays.
-- Apply through the Supabase SQL editor or your managed migration pipeline.
-- All access is performed server-side with the service-role key; never expose it to clients.

create extension if not exists pgcrypto;

create table if not exists public.agent_repository_overlays (
    id uuid primary key default gen_random_uuid(),
    repo_full_name text not null unique,
    repo_url text not null,
    default_branch text not null,
    enabled boolean not null default false,
    is_base boolean not null default false,
    scan_status text not null default 'not_scanned'
        check (scan_status in ('not_scanned', 'queued', 'completed', 'failed')),
    scan_sha text,
    scan_candidate_count integer not null default 0 check (scan_candidate_count >= 0),
    last_scanned_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint agent_repository_overlay_https check (repo_url like 'https://github.com/%')
);

create unique index if not exists agent_repository_overlays_single_base
    on public.agent_repository_overlays (is_base)
    where is_base = true;

create table if not exists public.agent_overlay_candidates (
    id uuid primary key default gen_random_uuid(),
    repository_id uuid not null references public.agent_repository_overlays(id) on delete cascade,
    kind text not null check (kind in ('skill', 'ui')),
    path text not null,
    name text not null,
    description text not null default '',
    source_url text not null,
    source_sha text not null,
    confidence numeric(4,3) not null default 0.5 check (confidence >= 0 and confidence <= 1),
    risk_flags text[] not null default '{}',
    manifest_state text not null default 'source_review',
    tags text[] not null default '{}',
    is_active boolean not null default false,
    created_at timestamptz not null default now(),
    unique(repository_id, kind, path),
    constraint agent_overlay_candidate_https check (source_url like 'https://github.com/%')
);

create index if not exists agent_overlay_candidates_runtime_idx
    on public.agent_overlay_candidates (repository_id, is_active, kind);

alter table public.agent_repository_overlays enable row level security;
alter table public.agent_overlay_candidates enable row level security;

-- No anon/authenticated policies are intentionally created.
-- The application server accesses these tables using SUPABASE_SERVICE_ROLE_KEY only.

insert into public.agent_repository_overlays
    (repo_full_name, repo_url, default_branch, enabled, is_base, scan_status)
values
    ('faerkan88228-pixel/OpenManus',
     'https://github.com/faerkan88228-pixel/OpenManus',
     'main', true, true, 'not_scanned')
on conflict (repo_full_name) do update
set repo_url = excluded.repo_url,
    is_base = true,
    enabled = true,
    updated_at = now();
