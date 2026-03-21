"""博主数据访问。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories.models import Creator


class CreatorRepository:
    @staticmethod
    def get_by_id(session: Session, creator_id: int) -> Creator | None:
        return session.get(Creator, creator_id)

    @staticmethod
    def get_by_stable_user_id(session: Session, stable_user_id: str) -> Creator | None:
        stmt = select(Creator).where(Creator.stable_user_id == stable_user_id)
        return session.scalar(stmt)

    @staticmethod
    def list_all(session: Session) -> list[Creator]:
        stmt = select(Creator).order_by(Creator.updated_at.desc())
        return list(session.scalars(stmt))

    @staticmethod
    def save(session: Session, creator: Creator) -> Creator:
        session.add(creator)
        session.flush()
        return creator
