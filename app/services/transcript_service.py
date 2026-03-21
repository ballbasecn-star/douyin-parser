"""
视频转录模块 - 从视频中提取语音文案

支持两种模式:
1. 本地模式 (默认): 使用 faster-whisper 本地转录
2. 云端模式 (--cloud): 使用 Groq Whisper API

优化: 使用 ffmpeg 直接从 URL 提取音频流，跳过视频轨道下载，
数据量减少 90%+，大幅提升速度。
"""
import logging
import os
from typing import Optional

from app.infra.media_tools import download_video, extract_audio_from_file, extract_audio_from_url

logger = logging.getLogger(__name__)


def transcribe_local(audio_path: str, model_size: str = "large-v3") -> Optional[str]:
    """
    使用 faster-whisper 本地转录

    Args:
        audio_path: 音频文件路径
        model_size: 模型大小 (tiny/base/small/medium/large-v3)

    Returns:
        转录文本，失败返回 None
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.error("faster-whisper 未安装，请运行: pip install faster-whisper")
        return None

    try:
        logger.info(f"加载模型 {model_size}...")
        model = WhisperModel(model_size, compute_type="int8")

        logger.info("转录中...")
        segments, info = model.transcribe(
            audio_path,
            language="zh",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
        )

        texts = []
        for segment in segments:
            texts.append(segment.text.strip())

        full_text = "\n".join(texts)
        logger.info(f"转录完成: {len(full_text)} 字")
        return full_text

    except Exception as exc:
        logger.error("本地转录失败: %s", exc)
        return None


# 云端服务商配置
CLOUD_PROVIDERS = {
    "groq": {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1/audio/transcriptions",
        "model": "whisper-large-v3-turbo",
        "env_key": "GROQ_API_KEY",
        "signup": "https://console.groq.com/keys",
    },
    "siliconflow": {
        "name": "SiliconFlow",
        "url": "https://api.siliconflow.cn/v1/audio/transcriptions",
        "model": "FunAudioLLM/SenseVoiceSmall",
        "env_key": "SILICONFLOW_API_KEY",
        "signup": "https://cloud.siliconflow.cn",
    },
}


def transcribe_cloud(
    audio_path: str,
    api_key: str = None,
    cloud_provider: str = "groq",
) -> Optional[str]:
    """
    使用云端 Whisper API 转录（支持 Groq 和 SiliconFlow）

    Args:
        audio_path: 音频文件路径
        api_key: API Key（不传则从环境变量读取）
        cloud_provider: 云服务商 (groq / siliconflow)

    Returns:
        转录文本，失败返回 None
    """
    provider = CLOUD_PROVIDERS.get(cloud_provider)
    if not provider:
        logger.error("不支持的云服务商: %s，可选: %s", cloud_provider, ", ".join(CLOUD_PROVIDERS.keys()))
        return None

    api_key = api_key or os.environ.get(provider["env_key"])
    if not api_key:
        logger.error("%s 未设置。获取地址: %s", provider["env_key"], provider["signup"])
        return None

    try:
        import requests

        logger.info("调用 %s Whisper API...", provider["name"])

        headers = {"Authorization": f"Bearer {api_key}"}

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
            data = {
                "model": provider["model"],
                "language": "zh",
                "response_format": "text",
            }

            response = requests.post(
                provider["url"], headers=headers, files=files, data=data, timeout=300
            )

        if response.status_code == 200:
            text = response.text.strip()
            logger.info("%s 转录完成: %s 字", provider["name"], len(text))
            return text
        logger.error("%s API 错误: %s - %s", provider["name"], response.status_code, response.text[:200])

    except Exception as exc:
        logger.error("%s 转录失败: %s", provider["name"], exc)

    return None


def transcribe_video(
    video_url: str,
    use_cloud: bool = False,
    cloud_provider: str = "groq",
    model_size: str = "large-v3",
    cloud_api_key: str = None,
    is_direct_url: bool = False,
) -> Optional[str]:
    """
    完整流程: 提取音频 → 语音转文字

    优先使用 ffmpeg 直接从 URL 提取音频流（快速），
    失败则降级为下载完整视频再提取。

    Args:
        video_url: 视频下载链接
        use_cloud: 是否使用云端 API
        cloud_provider: 云服务商 (groq / siliconflow)
        model_size: 本地模型大小
        cloud_api_key: 云端 API Key
        is_direct_url: 是否为直接下载链接

    Returns:
        转录文本
    """
    audio_path = None
    video_path = None

    try:
        # 方案 A: ffmpeg 直接从 URL 提取音频（快速，只下载音频流）
        audio_path = extract_audio_from_url(video_url)

        # 方案 B: 降级 — 下载完整视频再提取音频
        if not audio_path:
            logger.warning("URL 直接提取失败，降级为下载完整视频...")
            video_path = download_video(video_url)
            if video_path:
                audio_path = extract_audio_from_file(video_path)

        if not audio_path:
            logger.error("音频提取失败")
            return None

        # 转录
        if use_cloud:
            return transcribe_cloud(audio_path, cloud_api_key, cloud_provider)
        else:
            return transcribe_local(audio_path, model_size)

    finally:
        for path in [audio_path, video_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                    logger.debug("清理临时文件: %s", path)
                except Exception:
                    pass
