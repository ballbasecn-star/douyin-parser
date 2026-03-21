import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.api.app_factory import create_app
from app.infra.db import reset_database_state
from app.schemas.video_parse import ParseRequest


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.db_file.close()
        self.previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_file.name}"
        reset_database_state()
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        reset_database_state()
        if self.previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.previous_database_url
        if os.path.exists(self.db_file.name):
            os.unlink(self.db_file.name)

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

    @patch("app.api.routes.create_creator")
    @patch("app.api.routes.parse_creator_create_request")
    def test_create_creator_returns_payload(self, mock_parse_creator_create_request, mock_create_creator):
        mock_parse_creator_create_request.return_value = Mock()
        mock_create_creator.return_value = {"creator": {"id": 1, "stable_user_id": "MS4w-test"}, "created": True}

        response = self.client.post("/api/creators", json={"source_url": "https://v.douyin.com/abc/"})

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["creator"]["id"], 1)

    @patch("app.api.routes.list_creators", return_value=[{"id": 1, "nickname": "林克"}])
    def test_list_creators_returns_payload(self, _mock_list_creators):
        response = self.client.get("/api/creators")

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"][0]["nickname"], "林克")

    @patch("app.api.routes.parse_stored_video_analyze_request")
    @patch("app.api.routes.analyze_stored_video")
    def test_video_analyze_returns_payload(self, mock_analyze_stored_video, mock_parse_request):
        mock_parse_request.return_value = Mock()
        mock_analyze_stored_video.return_value = {"id": 1, "status": "completed", "video": {"id": 2}}

        response = self.client.post("/api/videos/2/analyze", json={})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["status"], "completed")
