"""视频分析结果数据访问。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories.models import VideoAnalysis


class VideoAnalysisRepository:
    @staticmethod
    def get_by_video_id(session: Session, video_pk: int) -> VideoAnalysis | None:
        stmt = select(VideoAnalysis).where(VideoAnalysis.video_id == video_pk)
        return session.scalar(stmt)

    @staticmethod
    def save(session: Session, analysis: VideoAnalysis) -> VideoAnalysis:
        session.add(analysis)
        session.flush()
        return analysis
