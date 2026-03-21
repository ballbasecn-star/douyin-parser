"""
兼容层：主解析流程已迁移到 app.services。
"""

from app.services.video_parse_service import parse_video as parse

__all__ = ["parse"]
