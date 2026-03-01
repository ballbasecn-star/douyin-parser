"""
抖音视频解析器 - 主解析入口

完全本地化，不依赖任何远程中间服务。
直接请求抖音 API 获取数据。
"""
import logging
import os
from typing import Optional

from .models import VideoInfo
from .crawler import crawl_video, get_video_download_url

logger = logging.getLogger(__name__)


def parse(
    share_text: str,
    service_url: str = None,       # 保留接口兼容性，已不再使用
    enable_transcript: bool = True,
    use_cloud: bool = False,
    model_size: str = "large-v3",
    groq_api_key: str = None,
) -> Optional[VideoInfo]:
    """
    解析抖音视频信息

    Args:
        share_text: 分享文本或链接
        service_url: (已废弃) 远程服务地址
        enable_transcript: 是否转录视频内语音
        use_cloud: 是否使用 Groq 云端转录
        model_size: 本地转录模型大小
        groq_api_key: Groq API Key

    Returns:
        VideoInfo 对象，失败返回 None
    """
    if service_url:
        logger.warning("service_url 参数已废弃，现在使用完全本地化解析")

    # 1. 本地爬取视频信息
    result = crawl_video(share_text)
    if not result:
        return None

    video_info, raw_data = result

    # 2. 转录视频内语音
    if enable_transcript:
        try:
            from .transcriber import transcribe_video

            # 从 raw_data 中提取下载链接
            download_url = get_video_download_url(raw_data)
            if download_url:
                logger.info("开始转录视频内语音...")
                transcript = transcribe_video(
                    video_url=download_url,
                    use_cloud=use_cloud,
                    model_size=model_size,
                    groq_api_key=groq_api_key,
                    is_direct_url=True,  # 标记这是直接下载链接
                )
                if transcript:
                    video_info.transcript = transcript
                    logger.info("✅ 语音转录完成")
                else:
                    logger.warning("⚠️ 语音转录失败")
            else:
                logger.warning("⚠️ 无法获取视频下载链接，跳过转录")

        except ImportError as e:
            logger.warning(f"转录模块缺少依赖: {e}")
        except Exception as e:
            logger.error(f"转录失败: {e}")

    return video_info
