"""存量视频分析服务。"""

from __future__ import annotations

from app.infra.db import session_scope
from app.repositories.analysis_repository import VideoAnalysisRepository
from app.repositories.models import VideoAnalysis
from app.repositories.video_repository import CreatorVideoRepository
from app.schemas.creator_monitor import StoredVideoAnalyzeRequest
from app.services.video_parse_service import parse_video


def analyze_stored_video(video_pk: int, request: StoredVideoAnalyzeRequest) -> dict:
    """对已保存的视频执行转录与分析，并落库结果。"""
    with session_scope() as session:
        video = CreatorVideoRepository.get_by_id(session, video_pk)
        if video is None:
            raise ValueError("视频不存在")
        share_url = video.share_url

    result = parse_video(
        share_text=share_url,
        enable_transcript=request.enable_transcript,
        use_cloud=request.use_cloud,
        cloud_provider=request.cloud_provider,
        model_size=request.model_size,
        cloud_api_key=request.cloud_api_key,
        enable_analysis=request.enable_analysis,
        ai_model=request.ai_model,
    )

    with session_scope() as session:
        video = CreatorVideoRepository.get_by_id(session, video_pk)
        if video is None:
            raise ValueError("视频不存在")

        analysis = VideoAnalysisRepository.get_by_video_id(session, video.id)
        if analysis is None:
            analysis = VideoAnalysis(video_id=video.id)

        if result is None:
            analysis.status = "failed"
            analysis.error_message = "单视频解析失败，请检查链接或 Cookie 状态"
        else:
            video.title = result.title or video.title
            video.description = result.description or video.description
            video.cover_url = result.cover_url or video.cover_url
            video.play_count = result.play_count
            video.like_count = result.like_count
            video.comment_count = result.comment_count
            video.share_count = result.share_count
            video.collect_count = result.collect_count

            analysis.transcript = result.transcript
            analysis.analysis_json = result.analysis or {}
            analysis.transcript_provider = request.cloud_provider if request.use_cloud else "local"
            analysis.analysis_model = request.ai_model if request.enable_analysis else ""
            analysis.status = "completed"
            analysis.error_message = ""

        VideoAnalysisRepository.save(session, analysis)
        CreatorVideoRepository.save(session, video)

        payload = analysis.to_dict()
        payload["video"] = video.to_dict()
        return payload


def get_video_analysis(video_pk: int) -> dict:
    with session_scope() as session:
        video = CreatorVideoRepository.get_by_id(session, video_pk)
        if video is None:
            raise ValueError("视频不存在")

        analysis = VideoAnalysisRepository.get_by_video_id(session, video.id)
        if analysis is None:
            raise ValueError("该视频尚未生成分析结果")

        payload = analysis.to_dict()
        payload["video"] = video.to_dict()
        return payload
