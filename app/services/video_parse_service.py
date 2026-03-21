"""视频解析业务服务。"""

import logging
import os
from typing import Callable, Optional

from app.domain import VideoInfo
from app.schemas.video_parse import ParseRequest
from app.services.analysis_service import analyze_transcript
from app.services.transcript_service import transcribe_video
from app.services.video_fetch_service import crawl_video, get_video_download_url

logger = logging.getLogger(__name__)


def parse_video(
    share_text: str,
    service_url: Optional[str] = None,
    enable_transcript: bool = True,
    use_cloud: bool = False,
    cloud_provider: str = "groq",
    model_size: str = "large-v3",
    cloud_api_key: Optional[str] = None,
    enable_analysis: bool = False,
    ai_model: str = "Pro/deepseek-ai/DeepSeek-V3.2",
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> Optional[VideoInfo]:
    """执行单视频完整解析流程。"""

    def emit_log(message: str):
        logger.info(message)
        if progress_callback:
            progress_callback({"type": "log", "message": message})

    if service_url:
        logger.warning("service_url 参数已废弃，现在使用完全本地化解析")

    emit_log("开始解析抖音链接...")
    result = crawl_video(share_text)
    if not result:
        emit_log("❌ 视频链接解析失败。")
        return None

    video_info, raw_data = result

    if progress_callback:
        progress_callback({
            "type": "data",
            "step": "video_info",
            "data": video_info.to_dict(),
        })

    emit_log(f"✅ 获取到视频基本信息: {video_info.title}")

    if enable_transcript:
        try:
            download_url = get_video_download_url(raw_data)
            if download_url:
                mode = cloud_provider if use_cloud else f"本地 {model_size}"
                emit_log(f"开始转录视频语音 (使用 {mode})...")
                transcript = transcribe_video(
                    video_url=download_url,
                    use_cloud=use_cloud,
                    cloud_provider=cloud_provider,
                    model_size=model_size,
                    cloud_api_key=cloud_api_key,
                    is_direct_url=True,
                )
                if transcript:
                    video_info.transcript = transcript
                    emit_log("✅ 语音转录完成")
                    if progress_callback:
                        progress_callback({
                            "type": "data",
                            "step": "transcript",
                            "data": video_info.to_dict(),
                        })
                else:
                    emit_log("⚠️ 语音转录失败")
            else:
                emit_log("⚠️ 无法获取视频下载链接，跳过转录")
        except ImportError as exc:
            emit_log(f"⚠️ 转录模块缺少依赖: {exc}")
        except Exception as exc:
            emit_log(f"❌ 转录失败: {exc}")

    if enable_analysis and video_info.transcript:
        try:
            analysis_key = os.environ.get("SILICONFLOW_API_KEY") if cloud_api_key is None else cloud_api_key
            emit_log(f"🧠 正在请求大模型进行爆款深度拆解 ({ai_model})...")
            analysis_result = analyze_transcript(
                transcript=video_info.transcript,
                api_key=analysis_key,
                model=ai_model,
            )
            if analysis_result:
                video_info.analysis = analysis_result
                emit_log("✅ 爆款文案拆解完毕")
                if progress_callback:
                    progress_callback({
                        "type": "data",
                        "step": "analysis",
                        "data": video_info.to_dict(),
                    })
            else:
                emit_log("⚠️ 拆解失败，未返回结构化数据")
        except Exception as exc:
            emit_log(f"❌ 文案拆解失败: {exc}")

    emit_log("🎉 全部品工作流执行完毕！")
    return video_info


def run_video_parse(parse_request: ParseRequest, progress_callback=None):
    """执行单视频解析主流程。"""
    return parse_video(
        share_text=parse_request.url,
        enable_transcript=parse_request.enable_transcript,
        use_cloud=parse_request.use_cloud,
        cloud_provider=parse_request.cloud_provider,
        model_size=parse_request.model_size,
        cloud_api_key=parse_request.cloud_api_key,
        enable_analysis=parse_request.enable_analysis,
        ai_model=parse_request.ai_model,
        progress_callback=progress_callback,
    )
