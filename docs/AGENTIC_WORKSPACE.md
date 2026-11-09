# Agentic Workspace — operational setup

## What this adds

- OpenManus is the fixed base agent: faerkan88228-pixel/OpenManus.
- Additional GitHub repositories are optional overlays and can be enabled or disabled without changing the base repository.
- A scanner reads real GitHub repository metadata and the Git tree, then inspects candidate SKILL.md files and UI source files.
- The natural-language router ranks only discovered, enabled, manually activated candidates. It returns source paths and relevance evidence.
- Repository code is never imported, installed, evaluated, or executed by the scanner. UI modules are references for a reviewed integration/build step, not browser-side remote code.

## Required server configuration

Set these environment variables in the application hosting environment:

- SUPABASE_URL=https://<project-ref>.supabase.co
- SUPABASE_SERVICE_ROLE_KEY=<server-only service role key>
- WORKSPACE_ADMIN_TOKEN=<long random admin secret>
- GITHUB_TOKEN=<read-only GitHub token> (recommended for private repositories and API rate limits)
- CORS_ALLOWED_ORIGINS=https://<trusted-app-domain> (only when the browser UI is hosted on a different origin; same-origin is the default)

Do not place any of these values in HTML, JavaScript, source control, or browser storage. The browser receives only WORKSPACE_ADMIN_TOKEN entered for the current page session; Supabase and GitHub credentials remain server-side.

All outbound service URLs must use HTTPS on port 443. The app must be deployed behind a TLS reverse proxy on port 443; do not expose the FastAPI development port directly to the public internet.

## Database migration

Apply supabase/migrations/202611090001_agentic_workspace.sql using the Supabase SQL editor or the project's managed migration process. The migration creates the overlay and candidate tables, enables RLS without public policies, and seeds the fixed OpenManus base row.

## Operation

1. Open the Agentic Workspace tab and enter the server-configured workspace admin token.
2. On first connection, the workspace automatically scans the fixed OpenManus repository. Use its manual rescan control when you need to refresh it.
3. Add additional repositories with a GitHub HTTPS URL. The server scans them immediately and records the discovered candidates in Supabase.
4. Enable or disable each overlay repository. Disabling a repository immediately removes its candidates from natural-language routing while preserving their activation state for later re-enabling.
5. Open each candidate's GitHub source and explicitly confirm review before activation. Risk markers and incomplete skill frontmatter are highlighted, but every candidate requires confirmation.
6. Enter a natural-language task and build the pipeline. The response reports matched skills, UI modules, source links, and the policy gate.

## Original OpenManus runtime

The host application delegates execution to the original OpenManus agent through a separately deployed HTTP runtime. This separation is required because both codebases use the top-level Python package name `app`; importing both into one interpreter would cause module collisions.

- Runtime source: [faerkan88228-pixel/OpenManus](https://github.com/faerkan88228-pixel/OpenManus)
- Runtime adapter PR: [OpenManus PR #1](https://github.com/faerkan88228-pixel/OpenManus/pull/1) (draft; not merged)
- Runtime API: `POST /v1/agent/run`
- Host-to-runtime transport: HTTPS only, public port 443
- Required host secrets: `OPENMANUS_RUNTIME_URL`, `OPENMANUS_RUNTIME_TOKEN`
- Required runtime secret: `PROMETHEUS_RUNTIME_TOKEN` with the same value

The OpenManus runtime must be deployed from the reviewed runtime branch/PR and configured with a real `config/config.toml` containing the chosen model provider credentials. The example config is not a working provider connection.

## Execution boundary

The previous keyword-based local planner is no longer used for task execution. The runtime disables OpenManus' in-process Python execution tool by default; enabling it requires a separately isolated worker and explicit server-side opt-in. If the OpenManus runtime is not configured or unreachable, the task endpoint returns an error instead of reporting a simulated success.

The host fetches active skill and UI source files from GitHub at execution time and checks the Git blob SHA against the SHA recorded during scan/review. Changed sources are skipped until rescanned and reactivated. Repository code is not installed, imported, or injected into the browser; reviewed source content is supplied to OpenManus as bounded supplemental reference context.

When `GEMINI_API_KEY` is configured, repository scans generate 768-dimensional `gemini-embedding-001` document vectors, store them in Supabase pgvector, and query them with `RETRIEVAL_QUERY` embeddings. The router combines semantic similarity with lexical matching. The pipeline reports `hybrid_vector` when vector candidates are available and `lexical_fallback` when the key is absent or no vectors are indexed. Re-scan repositories after adding the key to populate embeddings.

The AI Studio URLs shown in the page are reference links only; they are not connected API integrations. Skill Builder draft generation and direct integrations with those AI Studio apps remain separate future work.
