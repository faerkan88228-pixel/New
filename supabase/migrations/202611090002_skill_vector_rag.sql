-- Semantic skill/UI retrieval using Gemini Embeddings + Supabase pgvector.
-- Requires the Agentic Workspace base migration 202611090001_agentic_workspace.sql.

create extension if not exists vector with schema extensions;

alter table public.agent_overlay_candidates
    add column if not exists embedding extensions.vector(768),
    add column if not exists embedding_model text,
    add column if not exists embedding_source_sha text;

create index if not exists agent_overlay_candidates_embedding_hnsw
    on public.agent_overlay_candidates
    using hnsw (embedding extensions.vector_cosine_ops)
    where embedding is not null;

create or replace function public.match_agent_overlay_candidates(
    query_embedding extensions.vector(768),
    match_count integer default 12,
    filter_repository_ids uuid[] default null
)
returns table (
    id uuid,
    repository_id uuid,
    kind text,
    path text,
    name text,
    description text,
    source_url text,
    source_sha text,
    confidence numeric,
    risk_flags text[],
    manifest_state text,
    is_active boolean,
    tags text[],
    similarity double precision
)
language sql
stable
set search_path = public, extensions
as $$
    select
        candidate.id,
        candidate.repository_id,
        candidate.kind,
        candidate.path,
        candidate.name,
        candidate.description,
        candidate.source_url,
        candidate.source_sha,
        candidate.confidence,
        candidate.risk_flags,
        candidate.manifest_state,
        candidate.is_active,
        candidate.tags,
        1 - (candidate.embedding <=> query_embedding) as similarity
    from public.agent_overlay_candidates as candidate
    inner join public.agent_repository_overlays as repository
        on repository.id = candidate.repository_id
    where candidate.embedding is not null
      and candidate.embedding_model = 'gemini-embedding-001'
      and candidate.embedding_source_sha = candidate.source_sha
      and candidate.is_active = true
      and repository.enabled = true
      and (
          filter_repository_ids is null
          or candidate.repository_id = any(filter_repository_ids)
      )
    order by candidate.embedding <=> query_embedding
    limit least(greatest(match_count, 1), 50);
$$;

revoke all on function public.match_agent_overlay_candidates(
    extensions.vector(768), integer, uuid[]
) from public, anon, authenticated;

grant execute on function public.match_agent_overlay_candidates(
    extensions.vector(768), integer, uuid[]
) to service_role;
