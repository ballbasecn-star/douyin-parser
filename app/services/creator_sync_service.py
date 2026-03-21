"""博主视频同步服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from app.infra.cookie_store import get_cookie_manager
from app.infra.db import session_scope
from app.infra.douyin_web_client import fetch_creator_posts
from app.repositories.creator_repository import CreatorRepository
from app.repositories.models import CreatorVideo
from app.repositories.video_repository import CreatorVideoRepository
from app.schemas.creator_monitor import CreatorSyncRequest
from app.services.video_fetch_service import parse_video_data


def _to_datetime(timestamp: int) -> datetime | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def _extract_creator_profile(raw_response: dict) -> dict:
    """从博主列表响应中尽量提取博主资料。"""
    for key in ("user", "user_info", "author"):
        value = raw_response.get(key)
        if isinstance(value, dict):
            user_obj = value.get("user") if isinstance(value.get("user"), dict) else value
            if isinstance(user_obj, dict):
                return user_obj
    return {}


def sync_creator_videos(creator_id: int, sync_request: CreatorSyncRequest | None = None) -> dict:
    """同步博主视频列表。"""
    request = sync_request or CreatorSyncRequest(max_cursor=0, count=20)

    with session_scope() as session:
        creator = CreatorRepository.get_by_id(session, creator_id)
        if creator is None:
            raise ValueError("博主不存在")
        creator_payload = creator.to_dict()

    cookie = get_cookie_manager().get_cookie()
    raw_response = fetch_creator_posts(
        stable_user_id=creator_payload["stable_user_id"],
        cookie=cookie,
        max_cursor=request.max_cursor,
        count=request.count,
        referer_url=creator_payload["resolved_url"],
    )
    if raw_response is None:
        raise ValueError("同步博主视频失败，请检查 Cookie 或主页链接是否可用")

    aweme_list = raw_response.get("aweme_list") or []
    synced_videos: list[dict] = []
    synced_count = 0
    now = datetime.now(timezone.utc)
    creator_profile = _extract_creator_profile(raw_response)

    with session_scope() as session:
        creator = CreatorRepository.get_by_id(session, creator_id)
        if creator is None:
            raise ValueError("博主不存在")

        if creator_profile:
            creator.nickname = creator_profile.get("nickname", creator.nickname)
            creator.display_handle = (
                creator_profile.get("unique_id", "")
                or creator_profile.get("short_id", "")
                or creator.display_handle
            )
            avatar = creator_profile.get("avatar_thumb", {}) or creator_profile.get("avatar_medium", {}) or {}
            avatar_urls = avatar.get("url_list", []) if isinstance(avatar, dict) else []
            if avatar_urls:
                creator.avatar_url = avatar_urls[0]

        for item in aweme_list:
            info = parse_video_data(item)
            video = CreatorVideoRepository.get_by_video_id(session, info.video_id)
            if video is None:
                video = CreatorVideo(
                    creator_id=creator.id,
                    video_id=info.video_id,
                    first_seen_at=now,
                )
            video.creator_id = creator.id
            video.title = info.title
            video.description = info.description
            video.share_url = info.share_url
            video.cover_url = info.cover_url or ""
            video.publish_time = _to_datetime(info.create_time)
            video.duration_ms = info.duration
            video.play_count = info.play_count
            video.like_count = info.like_count
            video.comment_count = info.comment_count
            video.share_count = info.share_count
            video.collect_count = info.collect_count
            video.last_synced_at = now
            video.raw_payload = item
            CreatorVideoRepository.save(session, video)
            synced_videos.append(video.to_dict())
            synced_count += 1

            author = item.get("author", {}) or {}
            if author:
                creator.nickname = author.get("nickname", creator.nickname)
                creator.display_handle = author.get("unique_id", "") or author.get("short_id", "") or creator.display_handle
                avatar = author.get("avatar_thumb", {}) or {}
                avatar_urls = avatar.get("url_list", []) if isinstance(avatar, dict) else []
                if avatar_urls:
                    creator.avatar_url = avatar_urls[0]

        if not aweme_list and not creator.nickname:
            raise ValueError("未获取到该博主的作品列表，可能是 Cookie 权限不足或主页接口仍需适配")

        creator.last_synced_at = now
        creator.sync_cursor = int(raw_response.get("max_cursor") or 0)
        CreatorRepository.save(session, creator)

        creator_data = creator.to_dict()

    return {
        "creator": creator_data,
        "synced_count": synced_count,
        "has_more": bool(raw_response.get("has_more")),
        "next_cursor": int(raw_response.get("max_cursor") or 0),
        "videos": synced_videos,
    }


def list_creator_videos(creator_id: int) -> list[dict]:
    with session_scope() as session:
        creator = CreatorRepository.get_by_id(session, creator_id)
        if creator is None:
            raise ValueError("博主不存在")
        videos = CreatorVideoRepository.list_by_creator(session, creator_id)
        return [video.to_dict() for video in videos]
