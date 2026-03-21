import unittest
from unittest.mock import Mock, patch

from app.api.app_factory import create_app
from app.schemas.video_parse import ParseRequest


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    @patch("app.api.routes.get_health_payload")
    def test_health_returns_payload(self, mock_get_health_payload):
        mock_get_health_payload.return_value = {
            "status": "running",
            "version": "1.0.0",
            "cookie": {"exists": True},
        }

        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "running")

    @patch("app.api.routes.run_video_parse")
    @patch("app.api.routes.parse_video_request")
    def test_parse_sync_returns_video_data(self, mock_parse_video_request, mock_run_video_parse):
        mock_parse_video_request.return_value = ParseRequest(
            url="https://www.douyin.com/video/123",
            enable_transcript=True,
            enable_analysis=True,
            use_cloud=True,
            cloud_provider="siliconflow",
            model_size="small",
            ai_model="Pro/deepseek-ai/DeepSeek-V3.2",
            cloud_api_key="sf-key",
        )
        result = Mock()
        result.to_dict.return_value = {"video_id": "123", "title": "测试视频"}
        mock_run_video_parse.return_value = result

        response = self.client.post(
            "/api/parse-sync",
            json={"url": "https://www.douyin.com/video/123"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["video_id"], "123")

    @patch("app.api.routes.parse_video_request", side_effect=ValueError("请输入抖音链接"))
    def test_parse_sync_returns_bad_request(self, _mock_parse_video_request):
        response = self.client.post("/api/parse-sync", json={})

        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "BAD_REQUEST")

    def test_cookie_set_requires_cookie(self):
        response = self.client.post("/api/cookie/set", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "请提供 Cookie")

    @patch("app.api.routes.save_runtime_keys", return_value=["SILICONFLOW_API_KEY"])
    def test_config_set_returns_saved_keys(self, _mock_save_runtime_keys):
        response = self.client.post("/api/config/set", json={"SILICONFLOW_API_KEY": "sf-key"})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertIn("SILICONFLOW_API_KEY", body["message"])
