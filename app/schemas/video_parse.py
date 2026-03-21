"""视频解析请求结构。"""

import os
from dataclasses import dataclass
from typing import Mapping, Optional

from app.infra.settings import DEFAULT_AI_MODEL


@dataclass(frozen=True)
class ParseRequest:
    """解析请求结构。"""

    url: str
    enable_transcript: bool
    enable_analysis: bool
    use_cloud: bool
    cloud_provider: str
    model_size: str
    ai_model: str
    cloud_api_key: Optional[str] = None


def parse_video_request(data: Optional[dict], environ: Optional[Mapping[str, str]] = None) -> ParseRequest:
    """标准化解析请求参数。"""
    if not data:
        raise ValueError("请提供 JSON 数据")

    env = environ or os.environ
    url = data.get("url", "").strip()
    if not url:
        raise ValueError("请输入抖音链接")

    use_cloud = bool(data.get("cloud", False))
    cloud_provider = data.get("cloud_provider", "groq")

    if use_cloud:
        if cloud_provider == "siliconflow":
            cloud_api_key = data.get("siliconflow_api_key") or env.get("SILICONFLOW_API_KEY")
        else:
            cloud_api_key = data.get("groq_api_key") or env.get("GROQ_API_KEY")
    else:
        cloud_api_key = None

    return ParseRequest(
        url=url,
        enable_transcript=bool(data.get("transcript", False)),
        enable_analysis=bool(data.get("analyze", False)),
        use_cloud=use_cloud,
        cloud_provider=cloud_provider,
        model_size=data.get("model", "small"),
        ai_model=data.get("ai_model", DEFAULT_AI_MODEL),
        cloud_api_key=cloud_api_key,
    )
