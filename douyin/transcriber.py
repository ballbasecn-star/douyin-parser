"""
视频转录模块 - 从视频中提取语音文案

支持两种模式:
1. 本地模式 (默认): 使用 faster-whisper 本地转录
2. 云端模式 (--cloud): 使用 Groq Whisper API
"""
import logging
import os
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def download_video(video_url: str, is_direct_url: bool = False) -> Optional[str]:
    """
    下载视频到临时文件

    Args:
        video_url: 视频下载链接（直接链接）
        is_direct_url: 是否为直接下载链接

    Returns:
        下载后的文件路径，失败返回 None
    """
    import requests

    try:
        logger.info("下载视频...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/130.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
        }

        response = requests.get(
            video_url,
            headers=headers,
            timeout=300,
            stream=True,
        )

        content_type = response.headers.get("Content-Type", "")

        if response.status_code == 200 and (
            "video" in content_type
            or "octet-stream" in content_type
            or is_direct_url  # 直接链接可能没有 Content-Type
        ):
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            size = 0
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
                size += len(chunk)
            tmp.close()

            if size > 1000:
                logger.info(f"视频下载完成: {tmp.name} ({size / 1024 / 1024:.1f}MB)")
                return tmp.name
            else:
                os.unlink(tmp.name)
                logger.warning("下载的文件过小，可能无效")
        else:
            logger.warning(f"下载失败: HTTP {response.status_code}, Content-Type: {content_type}")

    except Exception as e:
        logger.error(f"下载视频异常: {e}")

    return None


def extract_audio(video_path: str) -> Optional[str]:
    """
    从视频文件提取音频 (WAV 16kHz mono - Whisper 最佳输入格式)

    Args:
        video_path: 视频文件路径

    Returns:
        音频文件路径，失败返回 None
    """
    audio_path = video_path.rsplit(".", 1)[0] + ".wav"

    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn",                    # 不要视频
            "-acodec", "pcm_s16le",   # 16-bit PCM
            "-ar", "16000",           # 16kHz 采样率
            "-ac", "1",               # 单声道
            "-y",                     # 覆盖
            audio_path,
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )

        if result.returncode == 0 and os.path.exists(audio_path):
            size_mb = os.path.getsize(audio_path) / 1024 / 1024
            logger.info(f"音频提取完成: {audio_path} ({size_mb:.1f}MB)")
            return audio_path
        else:
            logger.error(f"ffmpeg 失败: {result.stderr[:200]}")

    except FileNotFoundError:
        logger.error("未找到 ffmpeg，请安装: brew install ffmpeg")
    except Exception as e:
        logger.error(f"音频提取异常: {e}")

    return None


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

    except Exception as e:
        logger.error(f"本地转录失败: {e}")
        return None


def transcribe_cloud(audio_path: str, api_key: str = None) -> Optional[str]:
    """
    使用 Groq Whisper API 云端转录

    Args:
        audio_path: 音频文件路径
        api_key: Groq API Key

    Returns:
        转录文本，失败返回 None
    """
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY 未设置。获取地址: https://console.groq.com/keys")
        return None

    try:
        import requests

        logger.info("调用 Groq Whisper API...")

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
            data = {
                "model": "whisper-large-v3-turbo",
                "language": "zh",
                "response_format": "text",
            }

            response = requests.post(
                url, headers=headers, files=files, data=data, timeout=120
            )

        if response.status_code == 200:
            text = response.text.strip()
            logger.info(f"云端转录完成: {len(text)} 字")
            return text
        else:
            logger.error(f"Groq API 错误: {response.status_code} - {response.text[:200]}")

    except Exception as e:
        logger.error(f"云端转录失败: {e}")

    return None


def transcribe_video(
    video_url: str,
    use_cloud: bool = False,
    model_size: str = "large-v3",
    groq_api_key: str = None,
    is_direct_url: bool = False,
) -> Optional[str]:
    """
    完整流程: 下载视频 → 提取音频 → 语音转文字

    Args:
        video_url: 视频下载链接
        use_cloud: 是否使用云端 API (Groq)
        model_size: 本地模型大小
        groq_api_key: Groq API Key
        is_direct_url: 是否为直接下载链接

    Returns:
        转录文本
    """
    video_path = None
    audio_path = None

    try:
        # Step 1: 下载视频
        video_path = download_video(video_url, is_direct_url=is_direct_url)
        if not video_path:
            logger.error("视频下载失败")
            return None

        # Step 2: 提取音频
        audio_path = extract_audio(video_path)
        if not audio_path:
            logger.error("音频提取失败")
            return None

        # Step 3: 转录
        if use_cloud:
            return transcribe_cloud(audio_path, groq_api_key)
        else:
            return transcribe_local(audio_path, model_size)

    finally:
        for path in [video_path, audio_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                    logger.debug(f"清理临时文件: {path}")
                except Exception:
                    pass
