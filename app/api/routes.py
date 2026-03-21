"""Web 页面与 HTTP API 路由。"""

import json
import logging
import queue
import threading

from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context

from app.schemas.video_parse import parse_video_request
from app.services.image_proxy_service import fetch_proxy_image
from app.services.system_service import (
    get_cookie_status_payload,
    get_health_payload,
    save_cookie_value,
    save_runtime_keys,
)
from app.services.video_parse_service import run_video_parse

api_blueprint = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


@api_blueprint.route("/")
def index():
    """主页。"""
    return render_template("index.html")


@api_blueprint.route("/api/health")
def health():
    """服务状态与 Cookie 状态。"""
    return jsonify(get_health_payload())


@api_blueprint.route("/api/parse", methods=["POST"])
def api_parse():
    """解析抖音视频并通过 SSE 返回进度。"""
    try:
        parse_request = parse_video_request(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    def generate():
        event_queue: queue.Queue = queue.Queue()

        def progress_callback(info):
            event_queue.put(info)

        def worker():
            try:
                result = run_video_parse(parse_request, progress_callback=progress_callback)
                if result:
                    event_queue.put({"type": "finish", "success": True})
                else:
                    event_queue.put(
                        {
                            "type": "finish",
                            "success": False,
                            "error": "解析失败，请检查链接是否有效",
                        }
                    )
            except Exception as exc:  # pragma: no cover - 兜底日志分支
                logger.error("API 解析错误: %s", exc)
                event_queue.put({"type": "finish", "success": False, "error": str(exc)})

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item = event_queue.get()
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            if item["type"] == "finish":
                break

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@api_blueprint.route("/api/parse-sync", methods=["POST"])
def api_parse_sync():
    """同步解析抖音视频，直接返回结构化 JSON。"""
    try:
        parse_request = parse_video_request(request.get_json(silent=True))
    except ValueError as exc:
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": str(exc),
                    },
                }
            ),
            400,
        )

    try:
        result = run_video_parse(parse_request)
        if not result:
            return (
                jsonify(
                    {
                        "success": False,
                        "data": None,
                        "error": {
                            "code": "PARSE_FAILED",
                            "message": "解析失败，请检查链接是否有效或 Cookie 是否可用",
                        },
                    }
                ),
                422,
            )

        return jsonify(
            {
                "success": True,
                "data": result.to_dict(),
                "error": None,
            }
        )
    except Exception as exc:  # pragma: no cover - 兜底日志分支
        logger.error("API 同步解析错误: %s", exc, exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(exc),
                    },
                }
            ),
            500,
        )


@api_blueprint.route("/api/cookie/status")
def cookie_status():
    """Cookie 状态。"""
    return jsonify(get_cookie_status_payload())


@api_blueprint.route("/api/cookie/set", methods=["POST"])
def cookie_set():
    """设置 Cookie。"""
    data = request.get_json(silent=True)
    cookie = (data or {}).get("cookie")
    if not cookie:
        return jsonify({"error": "请提供 Cookie"}), 400

    save_cookie_value(cookie)
    return jsonify({"success": True, "message": "Cookie 已保存"})


@api_blueprint.route("/api/proxy/image")
def proxy_image():
    """代理抖音 CDN 图片。"""
    image_url = request.args.get("url")
    if not image_url:
        return "Missing url", 400

    proxied = fetch_proxy_image(image_url)
    if proxied is None:
        return "Image not found", 404

    content, content_type, headers = proxied
    return Response(content, content_type=content_type, headers=headers)


@api_blueprint.route("/api/config/set", methods=["POST"])
def config_set():
    """将 API Key 存入当前进程环境变量。"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请提供数据"}), 400

    saved = save_runtime_keys(data)
    if not saved:
        return jsonify({"error": "未提供有效的 Key"}), 400

    return jsonify({"success": True, "message": f"已保存: {', '.join(saved)}"})
