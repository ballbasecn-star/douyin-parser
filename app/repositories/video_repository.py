"""博主视频数据访问。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.repositories.models import CreatorVideo


class CreatorVideoRepository:
    @staticmethod
    def get_by_id(session: Session, video_pk: int) -> CreatorVideo | None:
        stmt = select(CreatorVideo).options(selectinload(CreatorVideo.analysis)).where(CreatorVideo.id == video_pk)
        return session.scalar(stmt)

    @staticmethod
    def get_by_video_id(session: Session, video_id: str) -> CreatorVideo | None:
        stmt = select(CreatorVideo).where(CreatorVideo.video_id == video_id)
        return session.scalar(stmt)

    @staticmethod
    def list_by_creator(session: Session, creator_id: int) -> list[CreatorVideo]:
        stmt = (
            select(CreatorVideo)
            .options(selectinload(CreatorVideo.analysis))
            .where(CreatorVideo.creator_id == creator_id)
            .order_by(CreatorVideo.publish_time.desc().nullslast(), CreatorVideo.id.desc())
        )
        return list(session.scalars(stmt))

    @staticmethod
    def save(session: Session, video: CreatorVideo) -> CreatorVideo:
        session.add(video)
        session.flush()
        return video
