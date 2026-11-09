import os
import unittest

from fastapi import HTTPException

from app.agentic_workspace.runtime_client import runtime_endpoint, build_runtime_payload


class TestOpenManusRuntimeClient(unittest.TestCase):
    def setUp(self):
        self.old_url = os.environ.get("OPENMANUS_RUNTIME_URL")
        self.old_token = os.environ.get("OPENMANUS_RUNTIME_TOKEN")

    def tearDown(self):
        if self.old_url is None:
            os.environ.pop("OPENMANUS_RUNTIME_URL", None)
        else:
            os.environ["OPENMANUS_RUNTIME_URL"] = self.old_url
        if self.old_token is None:
            os.environ.pop("OPENMANUS_RUNTIME_TOKEN", None)
        else:
            os.environ["OPENMANUS_RUNTIME_TOKEN"] = self.old_token

    def test_requires_runtime_url_and_token(self):
        os.environ.pop("OPENMANUS_RUNTIME_URL", None)
        os.environ.pop("OPENMANUS_RUNTIME_TOKEN", None)
        with self.assertRaises(HTTPException) as error:
            runtime_endpoint()
        self.assertEqual(error.exception.status_code, 503)

    def test_rejects_non_https_runtime(self):
        os.environ["OPENMANUS_RUNTIME_URL"] = "http://runtime.example.com"
        os.environ["OPENMANUS_RUNTIME_TOKEN"] = "secret"
        with self.assertRaises(HTTPException) as error:
            runtime_endpoint()
        self.assertEqual(error.exception.status_code, 503)

    def test_accepts_https_runtime_on_port_443(self):
        os.environ["OPENMANUS_RUNTIME_URL"] = "https://runtime.example.com"
        os.environ["OPENMANUS_RUNTIME_TOKEN"] = "secret"
        self.assertEqual(runtime_endpoint(), ("https://runtime.example.com/v1/agent/run", "secret"))

    def test_builds_payload_with_reviewed_contexts(self):
        payload = build_runtime_payload(
            "Create a mobile dashboard",
            [{
                "kind": "ui",
                "name": "Dashboard",
                "source_url": "https://github.com/example/repo/blob/main/ui/Dashboard.tsx",
                "source_sha": "a" * 40,
                "content": "export default function Dashboard() {}",
            }],
        )
        self.assertEqual(payload["goal"], "Create a mobile dashboard")
        self.assertEqual(payload["skill_contexts"][0]["kind"], "ui")


if __name__ == "__main__":
    unittest.main()
