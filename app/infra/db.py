from __future__ import annotations

"""数据库基础设施。"""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infra.settings import DATA_DIR, get_database_url

_ENGINE = None
_SESSION_FACTORY = None
_ENGINE_URL = None


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


def _build_engine(database_url: str):
    engine_kwargs = {
        "future": True,
    }

    if database_url.startswith("sqlite"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool

    return create_engine(database_url, **engine_kwargs)


def get_engine():
    """懒加载数据库引擎，并在连接串变化时重建。"""
    global _ENGINE, _SESSION_FACTORY, _ENGINE_URL

    database_url = get_database_url()
    if _ENGINE is None or _SESSION_FACTORY is None or _ENGINE_URL != database_url:
        if _ENGINE is not None:
            _ENGINE.dispose()
        _ENGINE = _build_engine(database_url)
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, expire_on_commit=False)
        _ENGINE_URL = database_url
    return _ENGINE


def get_session() -> Session:
    """创建一个新的数据库会话。"""
    get_engine()
    return _SESSION_FACTORY()


@contextmanager
def session_scope() -> Iterator[Session]:
    """数据库事务上下文。"""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    """初始化数据库表结构。"""
    import app.repositories.models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def reset_database_state() -> None:
    """用于测试时重置全局数据库连接状态。"""
    global _ENGINE, _SESSION_FACTORY, _ENGINE_URL
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None
    _ENGINE_URL = None
