"""业务服务层。"""

from .video_fetch_service import crawl_video, get_video_download_url

__all__ = ["crawl_video", "get_video_download_url"]
