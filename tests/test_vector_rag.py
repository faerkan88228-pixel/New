import unittest

from app.agentic_workspace.service import AgenticWorkspaceService


class FakeEmbeddings:
    def __init__(self, configured):
        self.configured = configured
        self.calls = []

    async def embed_text(self, text, task_type):
        self.calls.append((text, task_type))
        return [0.1] * 768


class FakeStore:
    def __init__(self, candidate, vector_matches=None):
        self.candidate = candidate
        self.vector_matches = vector_matches or []
        self.match_calls = []

    async def list_repositories(self):
        return [
            {
                "id": "repo-1",
                "repo_full_name": "owner/repo",
                "default_branch": "main",
                "enabled": True,
            }
        ]

    async def list_candidates(self, repository_id):
        return [self.candidate]

    async def match_candidates(self, query_embedding, repository_ids):
        self.match_calls.append((query_embedding, repository_ids))
        return self.vector_matches


def make_candidate():
    return {
        "id": "candidate-1",
        "repository_id": "repo-1",
        "kind": "skill",
        "name": "Mobile UI Responsive Layout",
        "description": "Build responsive mobile-first application screens",
        "path": "skills/mobile/SKILL.md",
        "source_url": "https://github.com/owner/repo/blob/main/skills/mobile/SKILL.md",
        "source_sha": "a" * 40,
        "confidence": 0.9,
        "risk_flags": [],
        "manifest_state": "valid",
        "is_active": True,
        "tags": ["mobile", "responsive", "layout"],
    }


class TestVectorSkillRetrieval(unittest.IsolatedAsyncioTestCase):
    async def test_uses_gemini_query_and_supabase_vector_matches(self):
        candidate = make_candidate()
        service = AgenticWorkspaceService()
        service.store = FakeStore(
            candidate,
            vector_matches=[
                {
                    "id": "candidate-1",
                    "similarity": 0.82,
                }
            ],
        )
        service.embeddings = FakeEmbeddings(configured=True)

        ranked, mode = await service.ranked_candidates(
            "Create a responsive mobile dashboard"
        )

        self.assertEqual(mode, "hybrid_vector")
        self.assertEqual(ranked[0][1]["id"], "candidate-1")
        self.assertGreater(ranked[0][0], 0.5)
        self.assertEqual(service.embeddings.calls[0][1], "RETRIEVAL_QUERY")
        self.assertEqual(service.store.match_calls[0][1], ["repo-1"])

    async def test_uses_lexical_fallback_without_gemini_key(self):
        candidate = make_candidate()
        service = AgenticWorkspaceService()
        service.store = FakeStore(candidate)
        service.embeddings = FakeEmbeddings(configured=False)

        ranked, mode = await service.ranked_candidates(
            "Create a responsive mobile dashboard"
        )

        self.assertEqual(mode, "lexical_fallback")
        self.assertEqual(ranked[0][1]["id"], "candidate-1")
        self.assertEqual(service.store.match_calls, [])

    async def test_falls_back_lexically_when_no_vectors_are_indexed(self):
        candidate = make_candidate()
        service = AgenticWorkspaceService()
        service.store = FakeStore(candidate, vector_matches=[])
        service.embeddings = FakeEmbeddings(configured=True)

        ranked, mode = await service.ranked_candidates(
            "Create a responsive mobile dashboard"
        )

        self.assertEqual(mode, "lexical_fallback")
        self.assertEqual(ranked[0][1]["id"], "candidate-1")


if __name__ == "__main__":
    unittest.main()
