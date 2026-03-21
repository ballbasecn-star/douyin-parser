import unittest
from unittest.mock import patch

from app.services.analysis_service import analyze_transcript
from app.services.transcript_service import transcribe_video
from app.services.video_parse_service import parse_video
from douyin.analyzer import analyze_transcript as legacy_analyze_transcript
from douyin.parser import parse as legacy_parse
from douyin.transcriber import transcribe_video as legacy_transcribe_video


class TranscriptAndAnalysisCompatTests(unittest.TestCase):
    def test_legacy_transcriber_import_points_to_new_service(self):
        self.assertIs(legacy_transcribe_video, transcribe_video)

    def test_legacy_analyzer_import_points_to_new_service(self):
        self.assertIs(legacy_analyze_transcript, analyze_transcript)

    def test_legacy_parser_import_points_to_new_service(self):
        self.assertIs(legacy_parse, parse_video)

    @patch("app.services.video_parse_service.analyze_transcript")
    @patch("app.services.video_parse_service.transcribe_video")
    @patch("app.services.video_parse_service.get_video_download_url")
    @patch("app.services.video_parse_service.crawl_video")
    def test_parse_video_orchestrates_fetch_transcript_and_analysis(
        self,
        mock_crawl_video,
        mock_get_video_download_url,
        mock_transcribe_video,
        mock_analyze_transcript,
    ):
        class DummyVideoInfo:
            title = "测试视频"
            transcript = ""
            analysis = {}

            def to_dict(self):
                return {"title": self.title, "transcript": self.transcript, "analysis": self.analysis}

        video_info = DummyVideoInfo()
        mock_crawl_video.return_value = (video_info, {"video": {}})
        mock_get_video_download_url.return_value = "https://example.com/video.mp4"
        mock_transcribe_video.return_value = "这是完整文案"
        mock_analyze_transcript.return_value = {"hook_text": "开头一句"}

        result = parse_video(
            share_text="https://www.douyin.com/video/123",
            enable_transcript=True,
            use_cloud=True,
            cloud_provider="siliconflow",
            cloud_api_key="sf-key",
            enable_analysis=True,
            ai_model="Pro/deepseek-ai/DeepSeek-V3.2",
        )

        self.assertIs(result, video_info)
        self.assertEqual(video_info.transcript, "这是完整文案")
        self.assertEqual(video_info.analysis, {"hook_text": "开头一句"})
        mock_transcribe_video.assert_called_once()
        mock_analyze_transcript.assert_called_once_with(
            transcript="这是完整文案",
            api_key="sf-key",
            model="Pro/deepseek-ai/DeepSeek-V3.2",
        )


if __name__ == "__main__":
    unittest.main()
