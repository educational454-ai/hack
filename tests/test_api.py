"""Integration tests for FastAPI endpoints."""

import unittest
from fastapi.testclient import TestClient
from api.main import app


class TestFastAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("docs_url", res.json())

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("llm_model", data)

    def test_analyze_subjective_claim(self):
        res = self.client.post("/api/analyze", json={"claim": "Modi is a protagonist."})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "subjective_opinion")
        self.assertEqual(data["claim_type"], "subjective_opinion")
        self.assertIn("interpretive", data["explanation"].lower())

    def test_empty_claim_validation(self):
        res = self.client.post("/api/analyze", json={"claim": ""})
        self.assertEqual(res.status_code, 422) # Unprocessable Entity from Pydantic min_length=3


if __name__ == "__main__":
    unittest.main()
