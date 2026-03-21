"""
抖音视频解析器 - 主解析入口

完全本地化，不依赖任何远程中间服务。
直接请求抖音 API 获取数据。
"""
import logging
import os
from typing import Optional, Callable

from app.domain import VideoInfo
from app.services.video_fetch_service import crawl_video, get_video_download_url

logger = logging.getLogger(__name__)


def parse(
    share_text: str,
    service_url: Optional[str] = None,       # 保留接口兼容性，已不再使用
    enable_transcript: bool = True,
    use_cloud: bool = False,
    cloud_provider: str = "groq",
    model_size: str = "large-v3",
    cloud_api_key: Optional[str] = None,
    enable_analysis: bool = False,
    ai_model: str = "Pro/deepseek-ai/DeepSeek-V3.2",
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> Optional[VideoInfo]:
    """
    解析抖音视频信息

    Args:
        share_text: 分享文本或链接
        service_url: (已废弃) 远程服务地址
        enable_transcript: 是否转录视频内语音
        use_cloud: 是否使用云端转录
        cloud_provider: 云服务商 (groq / siliconflow)
        model_size: 本地转录模型大小
        cloud_api_key: 云端 API Key
        enable_analysis: 是否进行爆款文案拆解 (AI 分析)
        ai_model: AI 拆解使用的模型名称
        progress_callback: 用于发送实时进度的回调函数，接收一个 dict

    Returns:
        VideoInfo 对象，失败返回 None
    """
    def emit_log(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback({"type": "log", "message": msg})

    if service_url:
        logger.warning("service_url 参数已废弃，现在使用完全本地化解析")

    # 1. 本地爬取视频信息
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
            "data": video_info.to_dict()
        })
        
    emit_log(f"✅ 获取到视频基本信息: {video_info.title}")

    # 2. 转录视频内语音
    if enable_transcript:
        try:
            from .transcriber import transcribe_video

            # 从 raw_data 中提取下载链接
            download_url = get_video_download_url(raw_data)
            if download_url:
                emit_log(f"开始转录视频语音 (使用 {cloud_provider if use_cloud else '本地 ' + model_size})...")
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
                            "data": video_info.to_dict()
                        })
                else:
                    emit_log("⚠️ 语音转录失败")
            else:
                emit_log("⚠️ 无法获取视频下载链接，跳过转录")

        except ImportError as e:
            emit_log(f"⚠️ 转录模块缺少依赖: {e}")
        except Exception as e:
            emit_log(f"❌ 转录失败: {e}")

    # 3. AI 爆款文案拆解 (仅在有文案内容，且开启了分析时进行)
    if enable_analysis and video_info.transcript:
        try:
            from .analyzer import analyze_transcript
            
            analysis_key = os.environ.get("SILICONFLOW_API_KEY") if cloud_api_key is None else cloud_api_key
            
            emit_log(f"🧠 正在请求大模型进行爆款深度拆解 ({ai_model})...")
            analysis_result = analyze_transcript(
                transcript=video_info.transcript,
                api_key=analysis_key,
                model=ai_model
            )
            if analysis_result:
                video_info.analysis = analysis_result
                emit_log("✅ 爆款文案拆解完毕")
                if progress_callback:
                    progress_callback({
                        "type": "data",
                        "step": "analysis",
                        "data": video_info.to_dict()
                    })
            else:
                emit_log("⚠️ 拆解失败，未返回结构化数据")
        except Exception as e:
            emit_log(f"❌ 文案拆解失败: {e}")
            
    emit_log("🎉 全部品工作流执行完毕！")

    return video_info
