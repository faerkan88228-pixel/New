"""
API Endpoint Integration Tests using FastAPI TestClient.
"""

import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root_index_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OmniNexus Studio", resp.text)

    def test_list_voices_endpoint(self):
        resp = self.client.get("/api/audio/voices")
        self.assertEqual(resp.status_code, 200)
        voices = resp.json()
        names = [v["name"] for v in voices]
        self.assertIn("Ryan", names)
        self.assertIn("Serena", names)

    def test_synthesize_speech_endpoint(self):
        resp = self.client.post("/api/audio/synthesize", json={
            "text": "Hello world from API endpoint test",
            "speaker": "Ryan",
            "language": "English"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("url", data)

    def test_android_device_endpoints(self):
        devs_resp = self.client.get("/api/android/devices")
        self.assertEqual(devs_resp.status_code, 200)
        devs = devs_resp.json()
        self.assertGreater(len(devs), 0)

        info_resp = self.client.get("/api/android/info")
        self.assertEqual(info_resp.status_code, 200)
        info = info_resp.json()
        self.assertTrue(info.get("is_rooted"))

        screen_resp = self.client.get("/api/android/screenshot")
        self.assertEqual(screen_resp.status_code, 200)
        self.assertIn("screenshot_base64", screen_resp.json())

    def test_gateway_models_endpoint(self):
        resp = self.client.get("/api/gateway/models")
        self.assertEqual(resp.status_code, 200)
        models = resp.json()
        m_ids = [m["id"] for m in models]
        self.assertIn("qwen-2.5-72b", m_ids)

    def test_comfyui_endpoints(self):
        nodes_resp = self.client.get("/api/comfyui/nodes")
        self.assertEqual(nodes_resp.status_code, 200)

        wf_resp = self.client.get("/api/comfyui/workflow/custom_voice")
        self.assertEqual(wf_resp.status_code, 200)
        self.assertIn("nodes", wf_resp.json())


if __name__ == "__main__":
    unittest.main()
