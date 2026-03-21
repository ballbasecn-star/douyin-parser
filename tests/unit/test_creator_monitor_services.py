import os
import tempfile
import unittest
from unittest.mock import patch

from app.infra.db import init_database, reset_database_state, session_scope
from app.repositories.models import Creator, CreatorVideo
from app.schemas.creator_monitor import CreatorCreateRequest, CreatorSyncRequest, StoredVideoAnalyzeRequest
from app.services.creator_service import create_creator
from app.services.creator_sync_service import list_creator_videos, sync_creator_videos
from app.services.video_analysis_service import analyze_stored_video


class CreatorMonitorServiceTests(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.db_file.close()
        self.previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_file.name}"
        reset_database_state()
        init_database()

    def tearDown(self):
        reset_database_state()
        if self.previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.previous_database_url
        if os.path.exists(self.db_file.name):
            os.unlink(self.db_file.name)

    @patch("app.services.creator_service.sync_creator_videos")
    @patch("app.services.creator_service.resolve_redirect_url")
    def test_create_creator_persists_stable_user_id(self, mock_resolve_redirect_url, mock_sync_creator_videos):
        mock_resolve_redirect_url.return_value = "https://www.douyin.com/user/MS4wLjABAAAA-test"
        mock_sync_creator_videos.return_value = {"synced_count": 0, "videos": [], "has_more": False, "next_cursor": 0}

        result = create_creator(
            CreatorCreateRequest(
                source_url="https://v.douyin.com/abc/",
                domain_tag="AI",
                remark="对标账号",
                status="active",
                initial_sync=True,
            )
        )

        self.assertEqual(result["creator"]["stable_user_id"], "MS4wLjABAAAA-test")
        self.assertEqual(result["creator"]["domain_tag"], "AI")
        self.assertEqual(result["sync"]["synced_count"], 0)

    @patch("app.services.creator_sync_service.fetch_creator_posts")
    def test_sync_creator_videos_upserts_video_rows(self, mock_fetch_creator_posts):
        with session_scope() as session:
            creator = Creator(
                source_url="https://v.douyin.com/creator/",
                resolved_url="https://www.douyin.com/user/MS4wLjABAAAA-sync",
                stable_user_id="MS4wLjABAAAA-sync",
                nickname="",
                status="active",
            )
            session.add(creator)
            session.flush()
            creator_id = creator.id

        mock_fetch_creator_posts.return_value = {
            "status_code": 0,
            "has_more": False,
            "max_cursor": 123,
            "aweme_list": [
                {
                    "aweme_id": "video-1",
                    "desc": "第一条视频 #AI",
                    "create_time": 1710000000,
                    "author": {
                        "nickname": "测试博主",
                        "unique_id": "link-ai",
                        "avatar_thumb": {"url_list": ["https://example.com/avatar.jpg"]},
                    },
                    "statistics": {
                        "play_count": 100,
                        "digg_count": 10,
                        "comment_count": 2,
                        "share_count": 1,
                        "collect_count": 3,
                    },
                    "video": {
                        "duration": 12000,
                        "cover": {"url_list": ["https://example.com/cover.jpg"]},
                    },
                }
            ],
        }

        result = sync_creator_videos(creator_id, CreatorSyncRequest(max_cursor=0, count=20))
        videos = list_creator_videos(creator_id)

        self.assertEqual(result["synced_count"], 1)
        self.assertEqual(result["creator"]["nickname"], "测试博主")
        self.assertEqual(videos[0]["video_id"], "video-1")
        self.assertEqual(videos[0]["like_count"], 10)

    @patch("app.services.video_analysis_service.parse_video")
    def test_analyze_stored_video_persists_analysis_result(self, mock_parse_video):
        with session_scope() as session:
            creator = Creator(
                source_url="https://v.douyin.com/creator/",
                resolved_url="https://www.douyin.com/user/MS4wLjABAAAA-analysis",
                stable_user_id="MS4wLjABAAAA-analysis",
                nickname="测试博主",
                status="active",
            )
            session.add(creator)
            session.flush()

            video = CreatorVideo(
                creator_id=creator.id,
                video_id="video-2",
                title="待分析视频",
                description="待分析视频",
                share_url="https://www.douyin.com/video/2",
            )
            session.add(video)
            session.flush()
            video_pk = video.id

        class DummyResult:
            title = "分析后标题"
            description = "完整文案"
            cover_url = "https://example.com/new-cover.jpg"
            play_count = 1000
            like_count = 100
            comment_count = 10
            share_count = 5
            collect_count = 8
            transcript = "这是完整转录"
            analysis = {"hook_text": "开头要更狠"}

        mock_parse_video.return_value = DummyResult()

        result = analyze_stored_video(
            video_pk,
            StoredVideoAnalyzeRequest(
                enable_transcript=True,
                enable_analysis=True,
                use_cloud=True,
                cloud_provider="siliconflow",
                model_size="small",
                ai_model="Pro/deepseek-ai/DeepSeek-V3.2",
                cloud_api_key="sf-key",
            ),
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["transcript"], "这是完整转录")
        self.assertEqual(result["analysis_json"]["hook_text"], "开头要更狠")


if __name__ == "__main__":
    unittest.main()
