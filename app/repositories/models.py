from __future__ import annotations

"""ORM 模型定义。"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class Creator(Base, TimestampMixin):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_url: Mapped[str] = mapped_column(Text, nullable=False)
    stable_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    display_handle: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    avatar_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    domain_tag: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    remark: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_cursor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    videos: Mapped[list["CreatorVideo"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_url": self.source_url,
            "resolved_url": self.resolved_url,
            "stable_user_id": self.stable_user_id,
            "nickname": self.nickname,
            "display_handle": self.display_handle,
            "avatar_url": self.avatar_url,
            "domain_tag": self.domain_tag,
            "remark": self.remark,
            "status": self.status,
            "last_synced_at": _isoformat(self.last_synced_at),
            "sync_cursor": self.sync_cursor,
            "created_at": _isoformat(self.created_at),
            "updated_at": _isoformat(self.updated_at),
        }


class CreatorVideo(Base, TimestampMixin):
    __tablename__ = "creator_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"), index=True, nullable=False)
    video_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    share_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    publish_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    collect_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    creator: Mapped[Creator] = relationship(back_populates="videos")
    analysis: Mapped[Optional["VideoAnalysis"]] = relationship(
        back_populates="video",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creator_id": self.creator_id,
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "share_url": self.share_url,
            "cover_url": self.cover_url,
            "publish_time": _isoformat(self.publish_time),
            "duration_ms": self.duration_ms,
            "play_count": self.play_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "collect_count": self.collect_count,
            "first_seen_at": _isoformat(self.first_seen_at),
            "last_synced_at": _isoformat(self.last_synced_at),
            "analysis_status": self.analysis.status if self.analysis else "idle",
            "created_at": _isoformat(self.created_at),
            "updated_at": _isoformat(self.updated_at),
        }


class VideoAnalysis(Base, TimestampMixin):
    __tablename__ = "video_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("creator_videos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    analysis_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    transcript_provider: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    analysis_model: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)

    video: Mapped[CreatorVideo] = relationship(back_populates="analysis")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "video_id": self.video_id,
            "transcript": self.transcript,
            "analysis_json": self.analysis_json,
            "transcript_provider": self.transcript_provider,
            "analysis_model": self.analysis_model,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": _isoformat(self.created_at),
            "updated_at": _isoformat(self.updated_at),
        }
