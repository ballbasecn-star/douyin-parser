"""
SiliconFlow 基础客户端
"""

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

SILICONFLOW_CHAT_URL = "https://api.siliconflow.cn/v1/chat/completions"


def create_chat_completion(
    messages: list[dict[str, Any]],
    api_key: str,
    model: str,
    response_format: Optional[dict[str, Any]] = None,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """调用 SiliconFlow chat completions 接口。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = response_format

    response = requests.post(
        SILICONFLOW_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    logger.debug("SiliconFlow chat completions 调用成功")
    return response.json()
