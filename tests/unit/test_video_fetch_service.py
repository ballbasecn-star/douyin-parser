import unittest

from app.services.video_fetch_service import extract_share_link, parse_video_data


class VideoFetchServiceTests(unittest.TestCase):
    def test_extract_share_link_prefers_short_link(self):
        text = "看看这个视频 https://v.douyin.com/abcDEF1/ 太强了"
        self.assertEqual(extract_share_link(text), "https://v.douyin.com/abcDEF1/")

    def test_parse_video_data_maps_statistics_and_hashtags(self):
        info = parse_video_data(
            {
                "aweme_id": "123",
                "desc": "测试标题 #AI #抖音",
                "create_time": 1700000000,
                "author": {
                    "nickname": "林克",
                    "unique_id": "linker",
                    "avatar_thumb": {"url_list": ["https://example.com/avatar.jpg"]},
                },
                "statistics": {
                    "play_count": 100,
                    "digg_count": 20,
                    "comment_count": 3,
                    "share_count": 4,
                    "collect_count": 5,
                },
                "video": {
                    "duration": 56000,
                    "cover": {"url_list": ["https://example.com/cover.jpg"]},
                },
            }
        )

        self.assertEqual(info.video_id, "123")
        self.assertEqual(info.author, "林克")
        self.assertEqual(info.author_id, "linker")
        self.assertEqual(info.play_count, 100)
        self.assertEqual(info.like_count, 20)
        self.assertEqual(info.cover_url, "https://example.com/cover.jpg")
        self.assertEqual(info.hashtags, ["#AI", "#抖音"])

if __name__ == "__main__":
    unittest.main()
