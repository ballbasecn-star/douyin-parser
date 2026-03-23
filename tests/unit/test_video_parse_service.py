import unittest
from unittest.mock import patch

from app.api.parser_contract import parse_contract_request
from app.schemas.video_parse import ParseRequest, parse_video_request
from app.services.video_parse_service import run_video_parse


class ParseVideoRequestTests(unittest.TestCase):
    def test_parse_video_request_reads_siliconflow_key_from_env(self):
        request = parse_video_request(
            {
                "url": "https://www.douyin.com/video/123",
                "transcript": True,
                "analyze": True,
                "cloud": True,
                "cloud_provider": "siliconflow",
            },
            environ={"SILICONFLOW_API_KEY": "sf-key"},
        )

        self.assertEqual(request.url, "https://www.douyin.com/video/123")
        self.assertTrue(request.enable_transcript)
        self.assertTrue(request.enable_analysis)
        self.assertTrue(request.use_cloud)
        self.assertEqual(request.cloud_provider, "siliconflow")
        self.assertEqual(request.cloud_api_key, "sf-key")

    def test_parse_video_request_requires_json(self):
        with self.assertRaisesRegex(ValueError, "请提供 JSON 数据"):
            parse_video_request(None)

    def test_parse_video_request_requires_url(self):
        with self.assertRaisesRegex(ValueError, "请输入抖音链接"):
            parse_video_request({"url": "   "})

    def test_contract_request_defaults_to_siliconflow_cloud_transcript(self):
        request = parse_contract_request(
            {
                "requestId": "req_contract",
                "input": {
                    "sourceUrl": "https://www.douyin.com/video/123",
                    "platformHint": "douyin",
                },
                "options": {
                    "fetchTranscript": True,
                    "deepAnalysis": False,
                },
            },
            environ={"SILICONFLOW_API_KEY": "sf-key"},
        )

        self.assertEqual(request.url, "https://www.douyin.com/video/123")
        self.assertTrue(request.enable_transcript)
        self.assertTrue(request.use_cloud)
        self.assertEqual(request.cloud_provider, "siliconflow")
        self.assertEqual(request.cloud_api_key, "sf-key")


class VideoParseServiceTests(unittest.TestCase):
    @patch("app.services.video_parse_service.parse_video")
    def test_run_video_parse_maps_request_to_core_parse(self, mock_parse_video):
        parse_request = ParseRequest(
            url="https://www.douyin.com/video/123",
            enable_transcript=True,
            enable_analysis=True,
            use_cloud=True,
            cloud_provider="siliconflow",
            model_size="small",
            ai_model="Pro/deepseek-ai/DeepSeek-V3.2",
            cloud_api_key="sf-key",
        )

        run_video_parse(parse_request)

        mock_parse_video.assert_called_once_with(
            share_text="https://www.douyin.com/video/123",
            enable_transcript=True,
            use_cloud=True,
            cloud_provider="siliconflow",
            model_size="small",
            cloud_api_key="sf-key",
            enable_analysis=True,
            ai_model="Pro/deepseek-ai/DeepSeek-V3.2",
            progress_callback=None,
        )
