"""
Douyin Parser - Web 服务

启动方式:
    python -m web.app [--port 8080] [--debug]
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime

from flask import Flask, request, jsonify, render_template, send_from_directory

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from douyin.parser import parse
from douyin.cookie_manager import get_cookie_manager, start_webhook_background

app = Flask(__name__,
            template_folder="templates",
            static_folder="static")

logger = logging.getLogger(__name__)

# ==================== 页面路由 ====================

@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


# ==================== API 路由 ====================

@app.route("/api/health")
def health():
    """服务状态 + Cookie 状态"""
    cm = get_cookie_manager()
    cookie_info = cm.get_cookie_info()
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "cookie": cookie_info,
    })


@app.route("/api/parse", methods=["POST"])
def api_parse():
    """解析抖音视频"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请提供 JSON 数据"}), 400

    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "请输入抖音链接"}), 400

    # 解析选项
    enable_transcript = data.get("transcript", False)
    use_cloud = data.get("cloud", False)
    cloud_provider = data.get("cloud_provider", "groq")
    model_size = data.get("model", "small")

    # 确定 API Key
    if use_cloud:
        if cloud_provider == "siliconflow":
            cloud_api_key = data.get("siliconflow_api_key") or os.environ.get("SILICONFLOW_API_KEY")
        else:
            cloud_api_key = data.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
    else:
        cloud_api_key = None

    try:
        result = parse(
            share_text=url,
            enable_transcript=enable_transcript,
            use_cloud=use_cloud,
            cloud_provider=cloud_provider,
            model_size=model_size,
            cloud_api_key=cloud_api_key,
        )

        if result:
            return jsonify({
                "success": True,
                "data": result.to_dict(),
            })
        else:
            return jsonify({
                "success": False,
                "error": "解析失败，请检查链接是否有效",
            }), 400

    except Exception as e:
        logger.error(f"API 解析错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/cookie/status")
def cookie_status():
    """Cookie 状态"""
    cm = get_cookie_manager()
    info = cm.get_cookie_info()
    return jsonify(info)


@app.route("/api/cookie/set", methods=["POST"])
def cookie_set():
    """设置 Cookie"""
    data = request.get_json()
    if not data or not data.get("cookie"):
        return jsonify({"error": "请提供 Cookie"}), 400

    cm = get_cookie_manager()
    cm.save_cookie(data["cookie"], source="web")
    return jsonify({"success": True, "message": "Cookie 已保存"})


@app.route("/api/proxy/image")
def proxy_image():
    """代理抖音 CDN 图片（绕过 Referer 限制）"""
    import requests as req

    image_url = request.args.get("url")
    if not image_url:
        return "Missing url", 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.douyin.com/",
        }
        resp = req.get(image_url, headers=headers, timeout=10, stream=True)
        if resp.status_code == 200:
            from flask import Response
            return Response(
                resp.content,
                content_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        pass

    return "Image not found", 404


@app.route("/api/config/set", methods=["POST"])
def config_set():
    """安全地存储 API Key 到服务器环境变量（运行时）"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请提供数据"}), 400

    saved = []
    for key in ["GROQ_API_KEY", "SILICONFLOW_API_KEY"]:
        if key in data and data[key]:
            os.environ[key] = data[key]
            saved.append(key)

    if saved:
        return jsonify({"success": True, "message": f"已保存: {', '.join(saved)}"})
    return jsonify({"error": "未提供有效的 Key"}), 400


# ==================== 启动 ====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Douyin Parser Web 服务")
    parser.add_argument("--port", type=int, default=8080, help="端口 (默认: 8080)")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--webhook-port", type=int, default=5555, help="Cookie Webhook 端口")
    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 后台启动 Cookie Webhook
    start_webhook_background(port=args.webhook_port)
    logger.info(f"🍪 Cookie Webhook 已在后台启动 (端口: {args.webhook_port})")

    # 启动 Web 服务
    print(f"\n🚀 Douyin Parser Web 服务启动")
    print(f"   🌐 http://localhost:{args.port}")
    print(f"   🍪 Cookie Webhook: http://0.0.0.0:{args.webhook_port}")
    print(f"   按 Ctrl+C 停止\n")

    app.run(host="0.0.0.0", port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
