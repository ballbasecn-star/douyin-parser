"""数据库 schema 的最小回归测试。"""

from sqlalchemy import BigInteger

from app.repositories.models import Creator


def test_creator_sync_cursor_uses_bigint():
    assert isinstance(Creator.__table__.c.sync_cursor.type, BigInteger)
