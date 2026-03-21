"""博主监控请求结构。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional

from app.infra.douyin_link_utils import normalize_creator_source_url
from app.infra.settings import DEFAULT_AI_MODEL


@dataclass(frozen=True)
class CreatorCreateRequest:
    source_url: str
    domain_tag: str
    remark: str
    status: str
    initial_sync: bool


@dataclass(frozen=True)
class CreatorUpdateRequest:
    domain_tag: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = None


@dataclass(frozen=True)
class CreatorSyncRequest:
    max_cursor: int
    count: int


@dataclass(frozen=True)
class StoredVideoAnalyzeRequest:
    enable_transcript: bool
    enable_analysis: bool
    use_cloud: bool
    cloud_provider: str
    model_size: str
    ai_model: str
    cloud_api_key: Optional[str] = None


def parse_creator_create_request(data: Optional[dict]) -> CreatorCreateRequest:
    if not data:
        raise ValueError("请提供 JSON 数据")

    source_url = normalize_creator_source_url((data.get("source_url") or data.get("url") or "").strip())
    if not source_url:
        raise ValueError("请输入博主主页链接")

    status = (data.get("status") or "active").strip() or "active"
    if status not in {"active", "paused"}:
        raise ValueError("status 仅支持 active 或 paused")

    return CreatorCreateRequest(
        source_url=source_url,
        domain_tag=(data.get("domain_tag") or "").strip(),
        remark=(data.get("remark") or "").strip(),
        status=status,
        initial_sync=bool(data.get("initial_sync", True)),
    )


def parse_creator_update_request(data: Optional[dict]) -> CreatorUpdateRequest:
    if not data:
        raise ValueError("请提供 JSON 数据")

    status = data.get("status")
    if status is not None:
        status = str(status).strip() or None
        if status not in {"active", "paused", None}:
            raise ValueError("status 仅支持 active 或 paused")

    return CreatorUpdateRequest(
        domain_tag=((data.get("domain_tag") or "").strip() if "domain_tag" in data else None),
        remark=((data.get("remark") or "").strip() if "remark" in data else None),
        status=status,
    )


def parse_creator_sync_request(data: Optional[dict]) -> CreatorSyncRequest:
    payload = data or {}
    count = int(payload.get("count", 20))
    if count <= 0 or count > 100:
        raise ValueError("count 必须在 1 到 100 之间")
    return CreatorSyncRequest(
        max_cursor=int(payload.get("max_cursor", 0)),
        count=count,
    )


def parse_stored_video_analyze_request(
    data: Optional[dict],
    environ: Optional[Mapping[str, str]] = None,
) -> StoredVideoAnalyzeRequest:
    payload = data or {}
    env = environ or os.environ

    use_cloud = bool(payload.get("cloud", True))
    cloud_provider = payload.get("cloud_provider", "siliconflow")
    enable_transcript = bool(payload.get("transcript", True))
    enable_analysis = bool(payload.get("analyze", True))

    if use_cloud:
        if cloud_provider == "siliconflow":
            cloud_api_key = payload.get("siliconflow_api_key") or env.get("SILICONFLOW_API_KEY")
        else:
            cloud_api_key = payload.get("groq_api_key") or env.get("GROQ_API_KEY")
    else:
        cloud_api_key = None

    if not enable_transcript and not enable_analysis:
        raise ValueError("transcript 和 analyze 不能同时关闭")

    return StoredVideoAnalyzeRequest(
        enable_transcript=enable_transcript,
        enable_analysis=enable_analysis,
        use_cloud=use_cloud,
        cloud_provider=cloud_provider,
        model_size=payload.get("model", "small"),
        ai_model=payload.get("ai_model", DEFAULT_AI_MODEL),
        cloud_api_key=cloud_api_key,
    )
