"""
兼容层：文案分析能力已迁移到 app.services。
"""

from app.services.analysis_service import SYSTEM_PROMPT, analyze_transcript

__all__ = ["SYSTEM_PROMPT", "analyze_transcript"]
