"""视频解析业务服务。"""

from douyin.parser import parse

from app.schemas.video_parse import ParseRequest


def run_video_parse(parse_request: ParseRequest, progress_callback=None):
    """执行单视频解析主流程。"""
    return parse(
        share_text=parse_request.url,
        enable_transcript=parse_request.enable_transcript,
        use_cloud=parse_request.use_cloud,
        cloud_provider=parse_request.cloud_provider,
        model_size=parse_request.model_size,
        cloud_api_key=parse_request.cloud_api_key,
        enable_analysis=parse_request.enable_analysis,
        ai_model=parse_request.ai_model,
        progress_callback=progress_callback,
    )
