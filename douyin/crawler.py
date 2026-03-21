"""
兼容层：视频抓取逻辑已迁移到 app.services / app.infra。
"""

from app.infra.douyin_web_client import (
    BASE_PARAMS,
    DEFAULT_HEADERS,
    MOBILE_HEADERS,
    POST_DETAIL_API,
    USER_AGENT,
    build_post_detail_params,
    extract_aweme_id,
    fetch_video_detail,
    gen_mstoken,
    resolve_short_url,
    sign_params,
)
from app.services.video_fetch_service import (
    FULL_URL_PATTERN,
    SHORT_URL_PATTERN,
    crawl_video,
    extract_share_link,
    get_video_download_url,
    parse_video_data,
)

__all__ = [
    "POST_DETAIL_API",
    "USER_AGENT",
    "DEFAULT_HEADERS",
    "BASE_PARAMS",
    "SHORT_URL_PATTERN",
    "FULL_URL_PATTERN",
    "MOBILE_HEADERS",
    "extract_share_link",
    "extract_aweme_id",
    "resolve_short_url",
    "gen_mstoken",
    "build_post_detail_params",
    "sign_params",
    "fetch_video_detail",
    "parse_video_data",
    "get_video_download_url",
    "crawl_video",
]
