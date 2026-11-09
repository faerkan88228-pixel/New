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
2. Scan the fixed OpenManus repository.
3. Add additional repositories with a GitHub HTTPS URL. The server scans them immediately and records the discovered candidates in Supabase.
4. Enable or disable each overlay repository. Disabling a repository immediately removes its candidates from natural-language routing while preserving their activation state for later re-enabling.
5. Activate individual candidates only after reviewing their source URL. Candidates with risk markers or incomplete skill frontmatter require explicit review confirmation.
6. Enter a natural-language task and build the pipeline. The response reports matched skills, UI modules, source links, and the policy gate.

## Important implementation boundary

The current OmniNexus task executor still contains a keyword-based planning implementation. This workspace adds real repository discovery, cloud-backed overlay management, capability activation, and relevance routing into the agent's task metadata. It does not claim that arbitrary third-party skill instructions or UI source code are executable runtime plugins. A subsequent engineering increment should replace the heuristic task planner with a governed model-driven planner and explicit tool contracts before enabling skill instruction execution.
