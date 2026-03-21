"""
兼容层：转录能力已迁移到 app.services / app.infra。
"""

from app.infra.media_tools import FFMPEG_HEADERS, download_video, extract_audio_from_file, extract_audio_from_url
from app.services.transcript_service import CLOUD_PROVIDERS, transcribe_cloud, transcribe_local, transcribe_video

__all__ = [
    "FFMPEG_HEADERS",
    "CLOUD_PROVIDERS",
    "download_video",
    "extract_audio_from_file",
    "extract_audio_from_url",
    "transcribe_cloud",
    "transcribe_local",
    "transcribe_video",
]
