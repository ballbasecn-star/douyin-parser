#!/usr/bin/env python3
"""
Douyin Parser 云端客户端

面向 skill / agent 的薄客户端，封装统一 parser 契约调用。

示例:
    python scripts/douyin_parser_client.py parse "https://www.douyin.com/video/123"
    python scripts/douyin_parser_client.py parse "分享文本" --transcript --analyze --cloud --cloud-provider siliconflow
    python scripts/douyin_parser_client.py health
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests


DEFAULT_BASE_URL = os.environ.get("DOUYIN_PARSER_BASE_URL", "http://127.0.0.1:8080")
DEFAULT_TIMEOUT = int(os.environ.get("DOUYIN_PARSER_TIMEOUT", "600"))
DEFAULT_AI_MODEL = "Pro/deepseek-ai/DeepSeek-V3.2"


def build_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def build_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def request_json(method: str, url: str, headers: Dict[str, str], timeout: int, payload: Optional[dict] = None) -> Dict[str, Any]:
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"请求失败: {exc}") from exc

    try:
        body = response.json()
    except ValueError as exc:
        snippet = response.text[:300] if response.text else ""
        raise RuntimeError(f"服务未返回合法 JSON (HTTP {response.status_code}): {snippet}") from exc

    if response.status_code >= 400:
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message") or json.dumps(error, ensure_ascii=False)
        else:
            message = body.get("message") or body.get("error") or response.reason
        raise RuntimeError(f"HTTP {response.status_code}: {message}")

    return body


def command_health(args: argparse.Namespace) -> int:
    result = request_json(
        method="GET",
        url=build_url(args.base_url, "/api/v1/health"),
        headers=build_headers(args.token),
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_parse(args: argparse.Namespace) -> int:
    payload = {
        "requestId": f"req_cli_{os.getpid()}",
        "input": {
            "sourceText": args.input_text,
            "sourceUrl": args.input_text if "http" in args.input_text else "",
            "platformHint": "douyin",
        },
        "options": {
            "fetchTranscript": args.transcript,
            "fetchMedia": True,
            "fetchMetrics": True,
            "deepAnalysis": args.analyze and args.transcript,
            "languageHint": "zh-CN",
        },
    }

    result = request_json(
        method="POST",
        url=build_url(args.base_url, "/api/v1/parse"),
        headers=build_headers(args.token),
        payload=payload,
        timeout=args.timeout,
    )

    if args.output == "data":
        print(json.dumps(result.get("data"), ensure_ascii=False, indent=2 if args.pretty else None))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Douyin Parser 云端客户端")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"服务基地址 (默认: {DEFAULT_BASE_URL})")
    parser.add_argument("--token", default=os.environ.get("DOUYIN_PARSER_TOKEN"), help="可选 Bearer Token")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"请求超时秒数 (默认: {DEFAULT_TIMEOUT})")
    parser.add_argument("--pretty", action="store_true", help="格式化输出 JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

    health_parser = subparsers.add_parser("health", help="检查服务状态")
    health_parser.set_defaults(func=command_health)

    parse_parser = subparsers.add_parser("parse", help="调用 /api/v1/parse 解析视频")
    parse_parser.add_argument("input_text", help="抖音分享文本或链接")
    parse_parser.add_argument("--transcript", action="store_true", help="启用语音转录")
    parse_parser.add_argument("--analyze", action="store_true", help="启用 AI 爆款分析")
    parse_parser.add_argument("--cloud", action="store_true", help="使用云端转录")
    parse_parser.add_argument("--cloud-provider", default="groq", choices=["groq", "siliconflow"], help="云端转录服务商")
    parse_parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v3"], help="本地 Whisper 模型")
    parse_parser.add_argument("--ai-model", default=DEFAULT_AI_MODEL, help="AI 分析模型")
    parse_parser.add_argument("--groq-api-key", default=os.environ.get("GROQ_API_KEY"), help="可选 Groq API Key")
    parse_parser.add_argument("--siliconflow-api-key", default=os.environ.get("SILICONFLOW_API_KEY"), help="可选 SiliconFlow API Key")
    parse_parser.add_argument("--output", default="response", choices=["response", "data"], help="输出完整响应或只输出 data")
    parse_parser.set_defaults(func=command_parse)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return args.func(args)
    except RuntimeError as exc:
        print(json.dumps({
            "success": False,
            "data": None,
            "error": {
                "code": "CLIENT_ERROR",
                "message": str(exc),
            }
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
