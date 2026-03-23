"""Web 页面与 HTTP API 路由。"""

import json
import logging
import queue
import threading

from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context

from app.schemas.creator_monitor import (
    parse_creator_create_request,
    parse_creator_sync_request,
    parse_creator_update_request,
    parse_stored_video_analyze_request,
)
from app.api.parser_contract import (
    build_capabilities_payload,
    build_health_payload as build_contract_health_payload,
    contract_error_response,
    contract_success_response,
    create_request_id,
    parse_contract_request,
    to_parsed_content_payload,
    UnsupportedUrlError,
)
from app.schemas.video_parse import parse_video_request
from app.services.creator_service import create_creator, get_creator_detail, list_creators, update_creator
from app.services.creator_sync_service import list_creator_videos, sync_creator_videos
from app.services.image_proxy_service import fetch_proxy_image
from app.services.system_service import (
    get_cookie_status_payload,
    get_health_payload,
    save_cookie_value,
    save_runtime_keys,
)
from app.services.video_analysis_service import analyze_stored_video, get_video_analysis
from app.services.video_parse_service import run_video_parse

api_blueprint = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


def success_response(data, status_code: int = 200):
    return jsonify({"success": True, "data": data, "error": None}), status_code


def error_response(code: str, message: str, status_code: int):
    return (
        jsonify(
            {
                "success": False,
                "data": None,
                "error": {"code": code, "message": message},
            }
        ),
        status_code,
    )


@api_blueprint.route("/")
def index():
    """主页。"""
    return render_template("index.html")


@api_blueprint.route("/api/health")
def health():
    """服务状态与 Cookie 状态。"""
    return jsonify(get_health_payload())


@api_blueprint.route("/api/v1/health")
def parser_health():
    """统一 parser 健康检查。"""
    return contract_success_response(create_request_id(), build_contract_health_payload())


@api_blueprint.route("/api/v1/capabilities")
def parser_capabilities():
    """统一 parser 能力声明。"""
    return contract_success_response(create_request_id(), build_capabilities_payload())


@api_blueprint.route("/api/v1/parse", methods=["POST"])
def parser_parse():
    """统一 parser 解析入口。"""
    request_body = request.get_json(silent=True)
    request_id = ((request_body or {}).get("requestId") or "").strip() or create_request_id()

    try:
        parse_request = parse_contract_request(request_body)
    except UnsupportedUrlError as exc:
        return contract_error_response(request_id, "UNSUPPORTED_URL", str(exc), 400, retryable=False)
    except ValueError as exc:
        return contract_error_response(request_id, "INVALID_INPUT", str(exc), 400, retryable=False)

    try:
        result = run_video_parse(parse_request)
        if not result:
            return contract_error_response(
                request_id,
                "UPSTREAM_CHANGED",
                "解析失败，请检查链接是否有效或 Cookie 是否可用",
                422,
                retryable=True,
            )

        payload = to_parsed_content_payload(
            result,
            ((request_body or {}).get("options") or {}).get("languageHint"),
        )
        return contract_success_response(request_id, payload)
    except Exception as exc:  # pragma: no cover - 兜底日志分支
        logger.error("统一 parser 解析错误: %s", exc, exc_info=True)
        return contract_error_response(request_id, "INTERNAL_ERROR", str(exc), 500, retryable=True)


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
        return error_response("BAD_REQUEST", str(exc), 400)

    try:
        result = run_video_parse(parse_request)
        if not result:
            return error_response("PARSE_FAILED", "解析失败，请检查链接是否有效或 Cookie 是否可用", 422)

        return success_response(result.to_dict())
    except Exception as exc:  # pragma: no cover - 兜底日志分支
        logger.error("API 同步解析错误: %s", exc, exc_info=True)
        return error_response("INTERNAL_ERROR", str(exc), 500)


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


@api_blueprint.route("/api/creators", methods=["GET"])
def creators_list():
    """获取博主列表。"""
    return success_response(list_creators())


@api_blueprint.route("/api/creators", methods=["POST"])
def creators_create():
    """添加博主。"""
    try:
        create_request = parse_creator_create_request(request.get_json(silent=True))
        return success_response(create_creator(create_request), 201)
    except ValueError as exc:
        return error_response("BAD_REQUEST", str(exc), 400)
    except Exception as exc:  # pragma: no cover - 兜底日志分支
        logger.error("创建博主失败: %s", exc, exc_info=True)
        return error_response("INTERNAL_ERROR", str(exc), 500)


@api_blueprint.route("/api/creators/<int:creator_id>", methods=["GET"])
def creators_detail(creator_id: int):
    """获取单个博主详情。"""
    try:
        return success_response(get_creator_detail(creator_id))
    except ValueError as exc:
        return error_response("NOT_FOUND", str(exc), 404)


@api_blueprint.route("/api/creators/<int:creator_id>", methods=["PATCH"])
def creators_update(creator_id: int):
    """更新博主。"""
    try:
        update_request = parse_creator_update_request(request.get_json(silent=True))
        return success_response(update_creator(creator_id, update_request))
    except ValueError as exc:
        status = 404 if "不存在" in str(exc) else 400
        code = "NOT_FOUND" if status == 404 else "BAD_REQUEST"
        return error_response(code, str(exc), status)


@api_blueprint.route("/api/creators/<int:creator_id>/sync", methods=["POST"])
def creators_sync(creator_id: int):
    """同步博主视频列表。"""
    try:
        sync_request = parse_creator_sync_request(request.get_json(silent=True))
        return success_response(sync_creator_videos(creator_id, sync_request))
    except ValueError as exc:
        status = 404 if "不存在" in str(exc) else 400
        code = "NOT_FOUND" if status == 404 else "BAD_REQUEST"
        return error_response(code, str(exc), status)
    except Exception as exc:  # pragma: no cover - 兜底日志分支
        logger.error("同步博主视频失败: %s", exc, exc_info=True)
        return error_response("INTERNAL_ERROR", str(exc), 500)


@api_blueprint.route("/api/creators/<int:creator_id>/videos", methods=["GET"])
def creators_videos(creator_id: int):
    """获取博主视频列表。"""
    try:
        return success_response(list_creator_videos(creator_id))
    except ValueError as exc:
        return error_response("NOT_FOUND", str(exc), 404)


@api_blueprint.route("/api/videos/<int:video_id>/analyze", methods=["POST"])
def videos_analyze(video_id: int):
    """对已保存视频执行转录与分析。"""
    try:
        analyze_request = parse_stored_video_analyze_request(request.get_json(silent=True))
        return success_response(analyze_stored_video(video_id, analyze_request))
    except ValueError as exc:
        status = 404 if "不存在" in str(exc) else 400
        code = "NOT_FOUND" if status == 404 else "BAD_REQUEST"
        return error_response(code, str(exc), status)
    except Exception as exc:  # pragma: no cover - 兜底日志分支
        logger.error("分析存量视频失败: %s", exc, exc_info=True)
        return error_response("INTERNAL_ERROR", str(exc), 500)


@api_blueprint.route("/api/videos/<int:video_id>/analysis", methods=["GET"])
def videos_analysis(video_id: int):
    """获取已保存视频分析结果。"""
    try:
        return success_response(get_video_analysis(video_id))
    except ValueError as exc:
        status = 404 if "不存在" in str(exc) or "尚未生成" in str(exc) else 400
        code = "NOT_FOUND" if status == 404 else "BAD_REQUEST"
        return error_response(code, str(exc), status)
