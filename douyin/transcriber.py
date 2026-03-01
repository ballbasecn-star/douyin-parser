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
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# 请求头，用于 ffmpeg 访问抖音视频 URL
FFMPEG_HEADERS = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.212 Safari/537.36\r\n"
    "Referer: https://www.douyin.com/\r\n"
)


def extract_audio_from_url(video_url: str) -> Optional[str]:
    """
    直接从视频 URL 提取音频（不下载视频文件）

    ffmpeg 只读取音频流，跳过视频轨道，数据量大幅减少。

    Args:
        video_url: 视频直链 URL

    Returns:
        音频文件路径，失败返回 None
    """
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name

    try:
        logger.info("⚡ 从 URL 直接提取音频流（跳过视频下载）...")

        cmd = [
            "ffmpeg",
            "-headers", FFMPEG_HEADERS,
            "-i", video_url,
            "-vn",                    # 不处理视频轨道
            "-acodec", "libmp3lame",  # MP3 压缩（大幅减小文件）
            "-ar", "16000",           # 16kHz 采样率
            "-ac", "1",               # 单声道
            "-b:a", "64k",            # 64kbps 比特率
            "-y",                     # 覆盖
            audio_path,
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )

        if result.returncode == 0 and os.path.exists(audio_path):
            size_kb = os.path.getsize(audio_path) / 1024
            logger.info(f"✅ 音频提取完成: {size_kb:.0f}KB")
            return audio_path
        else:
            # 提取 ffmpeg 错误信息的最后一行
            stderr = result.stderr.strip().split("\n")
            error_msg = stderr[-1] if stderr else "未知错误"
            logger.error(f"ffmpeg 失败: {error_msg}")

    except FileNotFoundError:
        logger.error("未找到 ffmpeg，请安装: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg 超时（120秒），视频可能过长或网络过慢")
    except Exception as e:
        logger.error(f"音频提取异常: {e}")

    # 清理失败的文件
    if os.path.exists(audio_path):
        os.unlink(audio_path)

    return None


def extract_audio_from_file(video_path: str) -> Optional[str]:
    """
    从本地视频文件提取音频（降级方案）

    Args:
        video_path: 本地视频文件路径

    Returns:
        音频文件路径，失败返回 None
    """
    audio_path = video_path.rsplit(".", 1)[0] + ".wav"

    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
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


def download_video(video_url: str) -> Optional[str]:
    """
    下载完整视频到临时文件（降级方案，仅在 ffmpeg URL 模式失败时使用）

    Args:
        video_url: 视频下载链接

    Returns:
        下载后的文件路径，失败返回 None
    """
    import requests

    try:
        logger.info("降级: 下载完整视频...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/90.0.4430.212 Safari/537.36",
            "Referer": "https://www.douyin.com/",
        }

        response = requests.get(
            video_url,
            headers=headers,
            timeout=300,
            stream=True,
        )

        if response.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            size = 0
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
                size += len(chunk)
            tmp.close()

            if size > 1000:
                logger.info(f"视频下载完成: ({size / 1024 / 1024:.1f}MB)")
                return tmp.name
            else:
                os.unlink(tmp.name)
                logger.warning("下载的文件过小")
        else:
            logger.warning(f"下载失败: HTTP {response.status_code}")

    except Exception as e:
        logger.error(f"下载视频异常: {e}")

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
        logger.error(f"不支持的云服务商: {cloud_provider}，可选: {', '.join(CLOUD_PROVIDERS.keys())}")
        return None

    api_key = api_key or os.environ.get(provider["env_key"])
    if not api_key:
        logger.error(f"{provider['env_key']} 未设置。获取地址: {provider['signup']}")
        return None

    try:
        import requests

        logger.info(f"调用 {provider['name']} Whisper API...")

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
            logger.info(f"{provider['name']} 转录完成: {len(text)} 字")
            return text
        else:
            logger.error(f"{provider['name']} API 错误: {response.status_code} - {response.text[:200]}")

    except Exception as e:
        logger.error(f"{provider['name']} 转录失败: {e}")

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
                    logger.debug(f"清理临时文件: {path}")
                except Exception:
                    pass
