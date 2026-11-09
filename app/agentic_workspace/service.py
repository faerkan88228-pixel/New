"""Repository overlays and natural-language skill routing for Agentic Workspace."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.agentic_workspace.embeddings import EMBEDDING_MODEL, GeminiEmbeddingProvider

BASE_REPOSITORY = "faerkan88228-pixel/OpenManus"
GITHUB_API = "https://api.github.com"
MAX_FILE_BYTES = 48000
MAX_SCAN_CANDIDATES = 60
MAX_RUNTIME_CONTEXTS = 8
MAX_RUNTIME_CONTEXT_CHARS = 12000
MAX_RUNTIME_TOTAL_CHARS = 32000
UI_EXTENSIONS = {".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss"}
UI_DIRS = {"ui", "components", "component", "design-system", "themes", "theme", "styles", "screens"}
SKILL_DIRS = {"skills", ".agents", ".claude"}
STOP_WORDS = {"для", "это", "как", "что", "при", "над", "под", "или", "and", "the", "for", "with", "from", "this", "that", "agent", "skill", "skills", "repo", "repository", "module", "модуль", "скилл", "навык", "создать", "сделать", "добавить", "использовать", "нужно", "задача", "система"}
RISK_PATTERNS = {
    "prompt_override": re.compile(r"ignore\s+(all\s+)?previous\s+instructions|reveal\s+(the\s+)?system\s+prompt", re.I),
    "credential_exfiltration": re.compile(r"exfiltrat(e|ion)|send\s+(all\s+)?(secrets|credentials|tokens)\s+to", re.I),
    "destructive_shell": re.compile(r"rm\s+-rf\s+/(?:\s|$)|curl\s+[^\n]+\|\s*(?:bash|sh)", re.I),
}


def normalize_github_repository(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail="Укажите GitHub-репозиторий.")
    if "://" not in raw and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", raw):
        owner, name = raw.split("/", 1)
        return owner + "/" + name.removesuffix(".git")
    parsed = urlparse(raw)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"github.com", "www.github.com"}
        or parsed.username
        or parsed.password
    ):
        raise HTTPException(status_code=422, detail="Разрешены только HTTPS-ссылки github.com без userinfo.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Некорректный порт GitHub URL.") from exc
    if port not in {None, 443} or parsed.query or parsed.fragment:
        raise HTTPException(status_code=422, detail="GitHub должен использовать HTTPS на порту 443 без query-параметров.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise HTTPException(status_code=422, detail="Нужна ссылка непосредственно на репозиторий: github.com/owner/repo.")
    owner, name = parts
    name = name.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise HTTPException(status_code=422, detail="Некорректный идентификатор GitHub-репозитория.")
    return owner + "/" + name


def parse_skill_frontmatter(content: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---(?:\s*\r?\n|$)", content, re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$", line)
        if item:
            key, value = item.group(1).lower().replace("-", "_"), item.group(2).strip()
            if value.startswith(("'", '"')) and value.endswith(value[:1]):
                value = value[1:-1]
            fields[key] = value[:1000]
    return fields


def candidate_risk_flags(content: str) -> list[str]:
    return [name for name, pattern in RISK_PATTERNS.items() if pattern.search(content or "")]


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-zа-яё0-9_+-]{2,}", (value or "").lower()) if token not in STOP_WORDS}


def score_candidate(goal: str, candidate: dict[str, Any]) -> tuple[float, list[str]]:
    query_tokens = _tokens(goal)
    tags = candidate.get("tags", [])
    tag_text = " ".join(tags) if isinstance(tags, list) else ""
    text = " ".join([str(candidate.get("name", "")), str(candidate.get("description", "")), tag_text, str(candidate.get("path", ""))])
    candidate_tokens = _tokens(text)
    matched = sorted(query_tokens & candidate_tokens)
    if not query_tokens or not candidate_tokens or not matched:
        return 0.0, matched
    precision, recall = len(matched) / len(candidate_tokens), len(matched) / len(query_tokens)
    harmonic = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    phrase_bonus = 0.12 if any(token in text.lower() for token in query_tokens if len(token) > 4) else 0.0
    return min(0.99, harmonic + phrase_bonus), matched


def _require_admin(token: str | None) -> None:
    configured = os.getenv("WORKSPACE_ADMIN_TOKEN", "")
    if not configured:
        raise HTTPException(status_code=503, detail="Не настроен WORKSPACE_ADMIN_TOKEN на сервере.")
    if not token or not hmac.compare_digest(token, configured):
        raise HTTPException(status_code=401, detail="Нужен действительный токен администратора Workspace.")


class AddRepositoryRequest(BaseModel):
    url: str = Field(min_length=3, max_length=500)
    branch: str | None = Field(default=None, max_length=200)


class ToggleRequest(BaseModel):
    enabled: bool


class CandidateToggleRequest(BaseModel):
    enabled: bool
    confirm_review: bool = False


class PipelineRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=6000)


class SupabaseStore:
    def _configuration(self) -> tuple[str, str]:
        base = os.getenv("SUPABASE_URL", "").rstrip("/")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        parsed = urlparse(base)
        try:
            port = parsed.port
        except ValueError as exc:
            raise HTTPException(status_code=503, detail="Некорректный порт SUPABASE_URL.") from exc
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or port not in {None, 443}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise HTTPException(status_code=503, detail="Настройте SUPABASE_URL как HTTPS origin на порту 443.")
        if not key:
            raise HTTPException(status_code=503, detail="Не настроен SUPABASE_SERVICE_ROLE_KEY.")
        return base, key

    async def request(self, method: str, table: str, *, params: dict[str, Any] | None = None, body: Any = None, prefer: str | None = None) -> Any:
        base, key = self._configuration()
        headers = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            response = await client.request(method, base + "/rest/v1/" + table, headers=headers, params=params, json=body)
        if response.status_code >= 400:
            detail = "Ошибка Supabase REST API (" + str(response.status_code) + ")."
            if response.status_code in {404, 406}:
                detail += " Проверьте применение SQL-миграции Agentic Workspace."
            raise HTTPException(status_code=502, detail=detail)
        if not response.content:
            return []
        try:
            return response.json()
        except ValueError:
            return []

    async def list_repositories(self) -> list[dict[str, Any]]:
        return await self.request("GET", "agent_repository_overlays", params={"select": "*", "order": "is_base.desc,created_at.asc"})

    async def get_repository(self, repository_id: str) -> dict[str, Any] | None:
        rows = await self.request("GET", "agent_repository_overlays", params={"select": "*", "id": "eq." + repository_id, "limit": "1"})
        return rows[0] if rows else None

    async def find_repository(self, full_name: str) -> dict[str, Any] | None:
        rows = await self.request("GET", "agent_repository_overlays", params={"select": "*", "repo_full_name": "eq." + full_name, "limit": "1"})
        return rows[0] if rows else None

    async def upsert_repository(self, row: dict[str, Any]) -> dict[str, Any]:
        rows = await self.request("POST", "agent_repository_overlays", params={"on_conflict": "repo_full_name"}, body=row, prefer="resolution=merge-duplicates,return=representation")
        if rows:
            return rows[0]
        existing = await self.find_repository(row["repo_full_name"])
        if not existing:
            raise HTTPException(status_code=502, detail="Supabase не вернул запись репозитория.")
        return existing

    async def update_repository(self, repository_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
        rows = await self.request("PATCH", "agent_repository_overlays", params={"id": "eq." + repository_id}, body=row, prefer="return=representation")
        return rows[0] if rows else None

    async def delete_repository(self, repository_id: str) -> None:
        await self.request("DELETE", "agent_repository_overlays", params={"id": "eq." + repository_id})

    async def replace_candidates(self, repository_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        await self.request("DELETE", "agent_overlay_candidates", params={"repository_id": "eq." + repository_id})
        if not rows:
            return []
        return await self.request("POST", "agent_overlay_candidates", body=rows, prefer="return=representation")

    async def list_candidates(self, repository_id: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"select": "id,repository_id,kind,path,name,description,source_url,source_sha,confidence,risk_flags,manifest_state,is_active,tags,created_at"}
        if repository_id:
            params["repository_id"] = "eq." + repository_id
        return await self.request("GET", "agent_overlay_candidates", params=params)

    async def match_candidates(
        self, query_embedding: list[float], repository_ids: list[str]
    ) -> list[dict[str, Any]]:
        base, key = self._configuration()
        headers = {
            "apikey": key,
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        }
        body = {
            "query_embedding": query_embedding,
            "match_count": 20,
            "filter_repository_ids": repository_ids,
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            response = await client.post(
                base + "/rest/v1/rpc/match_agent_overlay_candidates",
                headers=headers,
                json=body,
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail="Supabase vector retrieval failed (" + str(response.status_code) + ").",
            )
        try:
            return response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=502, detail="Supabase vector retrieval returned invalid JSON."
            ) from exc

    async def get_candidate(self, candidate_id: str) -> dict[str, Any] | None:
        rows = await self.request("GET", "agent_overlay_candidates", params={"select": "*", "id": "eq." + candidate_id, "limit": "1"})
        return rows[0] if rows else None

    async def update_candidate(self, candidate_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
        rows = await self.request("PATCH", "agent_overlay_candidates", params={"id": "eq." + candidate_id}, body=row, prefer="return=representation")
        return rows[0] if rows else None


class GitHubScanner:
    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Prometheus-Agentic-Workspace"}
        token = os.getenv("GITHUB_TOKEN", "")
        if token:
            headers["Authorization"] = "Bearer " + token
        return headers

    async def get_json(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=False) as client:
            response = await client.get(GITHUB_API + path, headers=self._headers())
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub-репозиторий или файл не найден либо нет доступа.")
        if response.status_code == 403:
            raise HTTPException(status_code=502, detail="GitHub ограничил запрос: проверьте GITHUB_TOKEN и rate limit.")
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Ошибка GitHub API (" + str(response.status_code) + ").")
        return response.json()

    async def repository_metadata(self, full_name: str) -> dict[str, Any]:
        return await self.get_json("/repos/" + full_name)

    async def read_file(self, full_name: str, branch: str, path: str) -> str:
        endpoint = "/repos/" + full_name + "/contents/" + quote(path, safe="/") + "?ref=" + quote(branch, safe="")
        data = await self.get_json(endpoint)
        if data.get("encoding") != "base64":
            raise HTTPException(status_code=422, detail="GitHub не вернул текстовый файл в ожидаемом base64-формате.")
        import base64
        try:
            return base64.b64decode(data.get("content", ""), validate=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise HTTPException(status_code=422, detail="Файл репозитория не является корректным UTF-8 текстом.")

    async def scan(self, full_name: str, branch: str | None = None) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
        metadata = await self.repository_metadata(full_name)
        selected_branch = branch or metadata.get("default_branch")
        if not selected_branch or not re.fullmatch(r"[A-Za-z0-9._/-]{1,200}", selected_branch) or ".." in selected_branch or "//" in selected_branch:
            raise HTTPException(status_code=422, detail="Некорректное имя Git-ветки.")
        tree = await self.get_json("/repos/" + full_name + "/git/trees/" + quote(selected_branch, safe="/") + "?recursive=1")
        if tree.get("truncated"):
            raise HTTPException(status_code=422, detail="GitHub вернул усечённое дерево: сузьте репозиторий или выделите каталог навыков.")
        metadata["_tree_sha"] = tree.get("sha", "")
        paths: list[tuple[dict[str, Any], str]] = []
        for entry in tree.get("tree", []):
            path = entry.get("path", "")
            if entry.get("type") != "blob" or int(entry.get("size") or 0) > MAX_FILE_BYTES:
                continue
            parts = path.lower().split("/")
            filename = parts[-1]
            suffix = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
            if filename == "skill.md" or (suffix == ".md" and any(part in SKILL_DIRS for part in parts[:-1])):
                paths.append((entry, "skill"))
            elif suffix in UI_EXTENSIONS and any(part in UI_DIRS for part in parts[:-1]):
                paths.append((entry, "ui"))
            if len(paths) >= MAX_SCAN_CANDIDATES:
                break

        import asyncio
        semaphore = asyncio.Semaphore(8)

        async def inspect(entry: dict[str, Any], kind: str) -> dict[str, Any] | None:
            async with semaphore:
                path = entry["path"]
                try:
                    content = await self.read_file(full_name, selected_branch, path)
                except HTTPException as exc:
                    if exc.status_code == 404:
                        return None
                    raise
            if kind == "skill":
                fields = parse_skill_frontmatter(content)
                name = fields.get("name") or path.rsplit("/", 1)[-1].removesuffix(".md")
                description = fields.get("description", "")
                if not description:
                    paragraphs = [line.strip() for line in content.splitlines() if line.strip() and not line.lstrip().startswith(("#", "---"))]
                    description = paragraphs[0][:500] if paragraphs else "Файл навыка найден; требуется описание в frontmatter."
                manifest_state = "valid" if fields.get("name") and fields.get("description") else "manifest_review"
                confidence = 0.96 if manifest_state == "valid" else 0.65
                tags = [tag.strip() for tag in re.split(r"[,;]", fields.get("tags", "")) if tag.strip()]
            else:
                name = path.rsplit("/", 1)[-1]
                description = "Обнаружен UI-ресурс по реальному пути репозитория. Код не исполняется автоматически; требуется просмотр и интеграция."
                manifest_state = "source_review"
                confidence = 0.82 if path.lower().endswith((".tsx", ".jsx", ".vue", ".svelte")) else 0.72
                tags = [part for part in path.split("/")[:-1] if part.lower() in UI_DIRS]
            return {
                "kind": kind, "path": path, "name": name[:200], "description": description[:1000],
                "source_url": "https://github.com/" + full_name + "/blob/" + quote(selected_branch, safe="/") + "/" + quote(path, safe="/"),
                "source_sha": entry.get("sha", ""), "confidence": confidence,
                "risk_flags": candidate_risk_flags(content), "manifest_state": manifest_state,
                "tags": tags, "is_active": False,
                "_embedding_text": (name + "\\n" + description + "\\n" + path + "\\n" + content[:1800])[:3000],
            }

        built = await asyncio.gather(*(inspect(entry, kind) for entry, kind in paths))
        return metadata, selected_branch, [item for item in built if item]


def git_blob_sha1(content: str) -> str:
    raw = content.encode("utf-8")
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


class AgenticWorkspaceService:
    def __init__(self) -> None:
        self.store = SupabaseStore()
        self.scanner = GitHubScanner()
        self.embeddings = GeminiEmbeddingProvider()

    async def scan_repository(self, repository_id: str) -> dict[str, Any]:
        row = await self.store.get_repository(repository_id)
        if not row:
            raise HTTPException(status_code=404, detail="Репозиторий не найден.")
        try:
            metadata, branch, candidates = await self.scanner.scan(
                row["repo_full_name"], row.get("default_branch")
            )
            if self.embeddings.configured:
                import asyncio

                semaphore = asyncio.Semaphore(4)

                async def embed_candidate(item: dict[str, Any]) -> dict[str, Any]:
                    async with semaphore:
                        embedding = await self.embeddings.embed_text(
                            item.pop("_embedding_text", ""),
                            task_type="RETRIEVAL_DOCUMENT",
                        )
                    item["embedding"] = embedding
                    item["embedding_model"] = EMBEDDING_MODEL
                    item["embedding_source_sha"] = item["source_sha"]
                    return item

                candidates = await asyncio.gather(
                    *(embed_candidate(item) for item in candidates)
                )
            else:
                for item in candidates:
                    item.pop("_embedding_text", None)
                    item["embedding"] = None
                    item["embedding_model"] = None
                    item["embedding_source_sha"] = None
            stored = await self.store.replace_candidates(
                repository_id,
                [{"repository_id": repository_id, **item} for item in candidates],
            )
            updated = await self.store.update_repository(repository_id, {
                "default_branch": branch, "scan_status": "completed",
                "scan_sha": metadata.get("_tree_sha", ""),
                "scan_candidate_count": len(stored), "last_scanned_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            try:
                await self.store.update_repository(repository_id, {"scan_status": "failed"})
            except Exception:
                pass
            raise
        return {"repository": updated or row, "candidates": stored, "scan_count": len(stored)}

    async def ranked_candidates(
        self, goal: str
    ) -> tuple[list[tuple[float, dict[str, Any], list[str], float]], str]:
        repositories = await self.store.list_repositories()
        enabled = {
            row["id"]: row
            for row in repositories
            if row.get("enabled")
        }
        all_rows: list[dict[str, Any]] = []
        for repository_id in enabled:
            all_rows.extend(await self.store.list_candidates(repository_id))
        active_rows = {
            row["id"]: row
            for row in all_rows
            if row.get("is_active")
        }

        ranked: list[tuple[float, dict[str, Any], list[str], float]] = []
        retrieval_mode = "lexical_fallback"
        if self.embeddings.configured and enabled:
            query_embedding = await self.embeddings.embed_text(
                goal,
                task_type="RETRIEVAL_QUERY",
            )
            vector_matches = await self.store.match_candidates(
                query_embedding,
                list(enabled),
            )
            for vector_match in vector_matches:
                row = active_rows.get(vector_match["id"])
                if not row:
                    continue
                lexical_score, matched_terms = score_candidate(goal, row)
                semantic_score = max(
                    0.0,
                    min(1.0, float(vector_match.get("similarity", 0.0))),
                )
                combined_score = min(
                    0.99,
                    (0.8 * semantic_score) + (0.2 * lexical_score),
                )
                if combined_score >= 0.18:
                    ranked.append(
                        (combined_score, row, matched_terms, semantic_score)
                    )
            if ranked:
                retrieval_mode = "hybrid_vector"

        if not ranked:
            for row in active_rows.values():
                score, matched_terms = score_candidate(goal, row)
                if score >= 0.06:
                    ranked.append((score, row, matched_terms, 0.0))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked[:20], retrieval_mode

    async def runtime_bundle(self, goal: str) -> dict[str, Any]:
        ranked, retrieval_mode = await self.ranked_candidates(goal)
        capabilities = []
        for score, row, matched_terms, semantic_score in ranked[:12]:
            capabilities.append({
                "id": row["id"],
                "kind": row["kind"],
                "name": row["name"],
                "description": row["description"],
                "path": row["path"],
                "source_url": row["source_url"],
                "confidence": round(min(0.99, score), 3),
                "semantic_similarity": round(semantic_score, 4),
                "matched_terms": matched_terms,
            })

        repositories = await self.store.list_repositories()
        enabled = {
            row["id"]: row
            for row in repositories
            if row.get("enabled")
        }
        contexts: list[dict[str, Any]] = []
        total_chars = 0
        for _, candidate, _, _ in ranked:
            if len(contexts) >= MAX_RUNTIME_CONTEXTS:
                break
            repository = enabled.get(candidate["repository_id"])
            if not repository:
                continue
            try:
                content = await self.scanner.read_file(
                    repository["repo_full_name"],
                    repository["default_branch"],
                    candidate["path"],
                )
            except HTTPException as exc:
                if exc.status_code == 404:
                    continue
                raise
            if git_blob_sha1(content) != candidate.get("source_sha"):
                # The file changed after review/activation. It must be rescanned and reviewed.
                continue
            content_size = len(content.encode("utf-8"))
            if (
                content_size > MAX_RUNTIME_CONTEXT_CHARS
                or total_chars + content_size > MAX_RUNTIME_TOTAL_CHARS
            ):
                continue
            contexts.append({
                "kind": candidate["kind"],
                "name": candidate["name"],
                "source_url": candidate["source_url"],
                "source_sha": candidate["source_sha"],
                "content": content,
            })
            total_chars += content_size

        return {
            "capabilities": capabilities,
            "contexts": contexts,
            "retrieval_mode": retrieval_mode,
        }

    async def runtime_capabilities(self, goal: str) -> list[dict[str, Any]]:
        bundle = await self.runtime_bundle(goal)
        return bundle["capabilities"]

    async def runtime_contexts(self, goal: str) -> list[dict[str, Any]]:
        bundle = await self.runtime_bundle(goal)
        return bundle["contexts"]


workspace_service = AgenticWorkspaceService()
router = APIRouter(prefix="/api/workspace", tags=["Agentic Workspace"])


@router.get("/repositories")
async def list_workspace_repositories(x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    return {"repositories": await workspace_service.store.list_repositories()}


@router.post("/repositories")
async def add_workspace_repository(request: AddRepositoryRequest, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    full_name = normalize_github_repository(request.url)
    if full_name.lower() == BASE_REPOSITORY.lower():
        raise HTTPException(status_code=409, detail="OpenManus уже подключён как базовый репозиторий.")
    metadata = await workspace_service.scanner.repository_metadata(full_name)
    existing = await workspace_service.store.find_repository(full_name)
    row = await workspace_service.store.upsert_repository({
        "repo_full_name": full_name, "repo_url": "https://github.com/" + full_name,
        "default_branch": request.branch or metadata.get("default_branch", "main"),
        "enabled": existing.get("enabled", False) if existing else False,
        "is_base": False, "scan_status": "queued", "scan_candidate_count": 0,
    })
    result = await workspace_service.scan_repository(row["id"])
    return {"repository": result["repository"], "candidates": result["candidates"], "scan_count": result["scan_count"]}


@router.post("/repositories/{repository_id}/scan")
async def scan_workspace_repository(repository_id: str, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    return await workspace_service.scan_repository(repository_id)


@router.patch("/repositories/{repository_id}")
async def toggle_workspace_repository(repository_id: str, request: ToggleRequest, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    row = await workspace_service.store.get_repository(repository_id)
    if not row:
        raise HTTPException(status_code=404, detail="Репозиторий не найден.")
    if row.get("is_base") and not request.enabled:
        raise HTTPException(status_code=409, detail="Базовый OpenManus нельзя отключить.")
    return {"repository": await workspace_service.store.update_repository(repository_id, {"enabled": request.enabled})}


@router.delete("/repositories/{repository_id}")
async def delete_workspace_repository(repository_id: str, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    row = await workspace_service.store.get_repository(repository_id)
    if not row:
        raise HTTPException(status_code=404, detail="Репозиторий не найден.")
    if row.get("is_base"):
        raise HTTPException(status_code=409, detail="Базовый OpenManus нельзя удалить.")
    await workspace_service.store.delete_repository(repository_id)
    return {"deleted": True, "repo_full_name": row["repo_full_name"]}


@router.get("/candidates")
async def list_workspace_candidates(repository_id: str | None = None, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    rows = await workspace_service.store.list_candidates(repository_id)
    repositories = {row["id"]: row for row in await workspace_service.store.list_repositories()}
    for item in rows:
        parent = repositories.get(item["repository_id"], {})
        item["repository_name"] = parent.get("repo_full_name", "unknown")
        item["repository_enabled"] = bool(parent.get("enabled"))
    return {"candidates": rows}


@router.patch("/candidates/{candidate_id}")
async def toggle_workspace_candidate(candidate_id: str, request: CandidateToggleRequest, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    candidate = await workspace_service.store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Возможность не найдена.")
    repository = await workspace_service.store.get_repository(candidate["repository_id"])
    if not repository or not repository.get("enabled"):
        raise HTTPException(status_code=409, detail="Сначала включите репозиторий-источник.")
    if request.enabled and not request.confirm_review:
        raise HTTPException(status_code=409, detail="Перед активацией откройте исходный файл, проверьте его и подтвердите проверку.")
    return {"candidate": await workspace_service.store.update_candidate(candidate_id, {"is_active": request.enabled})}


@router.post("/pipeline")
async def build_workspace_pipeline(request: PipelineRequest, x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin")):
    _require_admin(x_workspace_admin)
    bundle = await workspace_service.runtime_bundle(request.goal)
    capabilities = bundle["capabilities"]
    retrieval_mode = bundle["retrieval_mode"]
    skills = [item for item in capabilities if item["kind"] == "skill"]
    ui_modules = [item for item in capabilities if item["kind"] == "ui"]
    return {
        "goal": request.goal,
        "status": "ready" if capabilities else "no_active_match",
        "retrieval_mode": retrieval_mode,
        "pipeline": [
            {"stage": "intent_analysis", "status": "completed", "detail": "Запрос принят и токенизирован."},
            {
                "stage": "semantic_retrieval",
                "status": "completed",
                "mode": retrieval_mode,
                "detail": (
                    "Gemini embeddings + Supabase pgvector + lexical reranking."
                    if retrieval_mode == "hybrid_vector"
                    else "GEMINI_API_KEY не настроен или векторные записи отсутствуют; используется lexical fallback."
                ),
            },
            {"stage": "repository_skill_search", "status": "completed", "selected": skills},
            {"stage": "ui_module_search", "status": "completed", "selected": ui_modules},
            {"stage": "policy_gate", "status": "awaiting_execution", "detail": "Перед запуском сервер повторно загружает источники и сверяет Git blob SHA; содержимое передаётся OpenManus как ограниченный контекст. Код overlay не устанавливается и не исполняется напрямую."},
        ],
        "selected_skills": skills,
        "selected_ui_modules": ui_modules,
        "message": (
            "Найдены активные возможности."
            if capabilities
            else "Нет активированных возможностей, релевантных запросу. Базовый OpenManus всё равно доступен."
        ),
    }


@router.post("/execute")
async def execute_workspace_pipeline(
    request: PipelineRequest,
    x_workspace_admin: str | None = Header(default=None, alias="X-Workspace-Admin"),
):
    _require_admin(x_workspace_admin)
    from app.agent.manus_core import manus_agent
    return await manus_agent.run_task("agentic-workspace", request.goal)


async def get_agent_runtime_bundle(goal: str) -> dict[str, Any]:
    """Return selected capabilities, verified source contexts, and retrieval mode."""
    return await workspace_service.runtime_bundle(goal)


async def get_agent_runtime_capabilities(goal: str) -> list[dict[str, Any]]:
    """Return metadata for active capabilities from enabled repository overlays."""
    return await workspace_service.runtime_capabilities(goal)


async def get_agent_runtime_contexts(goal: str) -> list[dict[str, Any]]:
    """Return source-integrity-verified content for the real OpenManus runtime."""
    return await workspace_service.runtime_contexts(goal)
