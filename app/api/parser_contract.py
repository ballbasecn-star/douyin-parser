"""统一 parser 契约适配。"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from uuid import uuid4

from flask import jsonify

from app.domain import VideoInfo
from app.infra.settings import APP_SEMANTIC_VERSION, APP_VERSION
from app.schemas.video_parse import ParseRequest

PARSER_VERSION = APP_SEMANTIC_VERSION or APP_VERSION or "0.1.0"
_SUPPORTED_HOST_KEYWORDS = ("douyin.com", "iesdouyin.com")


class UnsupportedUrlError(ValueError):
    """输入链接不属于当前 parser。"""


def create_request_id() -> str:
    return f"req_{uuid4().hex}"


def contract_success_response(request_id: str, data: Any, status_code: int = 200):
    return (
        jsonify(
            {
                "success": True,
                "data": data,
                "error": None,
                "meta": {
                    "requestId": request_id,
                    "parserVersion": PARSER_VERSION,
                },
            }
        ),
        status_code,
    )


def contract_error_response(
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    retryable: bool,
    details: Optional[dict[str, Any]] = None,
):
    error_payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    if details:
        error_payload["details"] = details

    return (
        jsonify(
            {
                "success": False,
                "data": None,
                "error": error_payload,
                "meta": {
                    "requestId": request_id,
                    "parserVersion": PARSER_VERSION,
                },
            }
        ),
        status_code,
    )


def build_health_payload() -> dict[str, str]:
    return {"status": "UP"}


def build_capabilities_payload() -> dict[str, Any]:
    return {
        "platform": "douyin",
        "supportedSourceTypes": ["video", "share_text"],
        "features": {
            "transcript": True,
            "images": True,
            "metrics": True,
            "authorProfile": False,
            "deepAnalysis": True,
            "batchParse": False,
            "asyncParse": False,
        },
    }


def parse_contract_request(data: Optional[dict], environ: Optional[Mapping[str, str]] = None) -> ParseRequest:
    if not data:
        raise ValueError("请提供 JSON 数据")

    input_payload = data.get("input") or {}
    options = data.get("options") or {}
    source_text = (input_payload.get("sourceText") or "").strip()
    source_url = (input_payload.get("sourceUrl") or "").strip()
    resolved_source = source_url or source_text

    if not resolved_source:
        raise ValueError("sourceText 和 sourceUrl 不能同时为空")
    if not looks_like_douyin_source(resolved_source):
        raise UnsupportedUrlError("当前 parser 仅支持抖音链接")

    fetch_transcript = options.get("fetchTranscript")
    enable_transcript = True if fetch_transcript is None else bool(fetch_transcript)
    deep_analysis = bool(options.get("deepAnalysis", False))

    from app.schemas.video_parse import parse_video_request

    # 线上主系统统一走云端转录，避免生产环境误落到本地转录链路。
    legacy_request = {
        "url": resolved_source,
        "transcript": enable_transcript,
        "analyze": deep_analysis and enable_transcript,
        "cloud": enable_transcript,
        "cloud_provider": "siliconflow",
        "model": "small",
    }
    return parse_video_request(legacy_request, environ=environ)


def looks_like_douyin_source(raw_value: str) -> bool:
    lowered = raw_value.lower()
    return any(keyword in lowered for keyword in _SUPPORTED_HOST_KEYWORDS)


def to_parsed_content_payload(video_info: VideoInfo, language_hint: Optional[str]) -> dict[str, Any]:
    canonical_url = video_info.share_url or ""
    if video_info.video_id:
        canonical_url = f"https://www.douyin.com/video/{video_info.video_id}"

    warnings = []
    if not video_info.transcript:
        warnings.append(
            {
                "code": "TRANSCRIPT_UNAVAILABLE",
                "message": "当前返回未包含语音转录文本。",
            }
        )
    if not video_info.analysis:
        warnings.append(
            {
                "code": "ANALYSIS_UNAVAILABLE",
                "message": "当前返回未包含爆款文案深度拆解结果。",
            }
        )

    return {
        "platform": "douyin",
        "sourceType": "video",
        "externalId": video_info.video_id or None,
        "canonicalUrl": canonical_url,
        "title": video_info.title or video_info.description or (video_info.video_id or "Douyin Video"),
        "summary": video_info.description or None,
        "author": {
            "externalAuthorId": video_info.author_id or None,
            "name": video_info.author or None,
            "handle": video_info.author_id or None,
            "profileUrl": None,
            "avatarUrl": video_info.author_avatar,
        },
        "publishedAt": _to_iso_utc(video_info.create_time),
        "language": language_hint or None,
        "content": {
            "rawText": video_info.description or video_info.title or None,
            "transcript": video_info.transcript or None,
            "segments": [],
        },
        "metrics": {
            "views": video_info.play_count or 0,
            "likes": video_info.like_count or 0,
            "comments": video_info.comment_count or 0,
            "shares": video_info.share_count or 0,
            "favorites": video_info.collect_count or 0,
        },
        "tags": video_info.hashtags,
        "media": {
            "covers": _compact_media([_media_item(video_info.cover_url, "image/jpeg")]),
            "images": [],
            "videos": _compact_media([_media_item(video_info.video_url, "video/mp4")]),
            "audios": [],
        },
        "rawPayload": {
            "analysis": video_info.analysis,
            "legacyVideoInfo": asdict(video_info),
        },
        "warnings": [warning for warning in warnings if warning],
    }


def _to_iso_utc(timestamp_value: int) -> Optional[str]:
    if not timestamp_value:
        return None
    try:
        return datetime.fromtimestamp(timestamp_value, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (OSError, OverflowError, ValueError):
        return None


def _media_item(url: Optional[str], mime_type: str) -> Optional[dict[str, Any]]:
    if not url:
        return None
    return {
        "url": url,
        "mimeType": mime_type,
        "width": None,
        "height": None,
        "durationMs": None,
    }


def _compact_media(items: list[Optional[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [item for item in items if item]
