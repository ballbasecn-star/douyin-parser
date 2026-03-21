"""博主管理服务。"""

from __future__ import annotations

from app.infra.db import session_scope
from app.infra.douyin_link_utils import normalize_creator_source_url
from app.infra.douyin_web_client import extract_stable_user_id, resolve_redirect_url
from app.repositories.creator_repository import CreatorRepository
from app.repositories.models import Creator
from app.schemas.creator_monitor import CreatorCreateRequest, CreatorUpdateRequest
from app.services.creator_sync_service import sync_creator_videos


def resolve_creator_identity(source_url: str) -> tuple[str, str]:
    """解析主页分享链接，返回稳定博主标识与最终链接。"""
    normalized_url = normalize_creator_source_url(source_url)
    if not normalized_url:
        raise ValueError("请输入有效的博主主页链接")

    resolved_candidate = resolve_redirect_url(normalized_url) or normalized_url
    stable_user_id = extract_stable_user_id(resolved_candidate)
    if not stable_user_id:
        raise ValueError("无法从主页链接中解析稳定博主标识，请确认链接是否有效")
    canonical_url = f"https://www.douyin.com/user/{stable_user_id}"
    return stable_user_id, canonical_url


def create_creator(request: CreatorCreateRequest) -> dict:
    """创建或更新博主。"""
    normalized_source_url = normalize_creator_source_url(request.source_url)
    stable_user_id, resolved_url = resolve_creator_identity(normalized_source_url)

    with session_scope() as session:
        creator = CreatorRepository.get_by_stable_user_id(session, stable_user_id)
        created = False
        if creator is None:
            creator = Creator(
                source_url=normalized_source_url,
                resolved_url=resolved_url,
                stable_user_id=stable_user_id,
                domain_tag=request.domain_tag,
                remark=request.remark,
                status=request.status,
            )
            CreatorRepository.save(session, creator)
            created = True
        else:
            creator.source_url = normalized_source_url
            creator.resolved_url = resolved_url
            if request.domain_tag:
                creator.domain_tag = request.domain_tag
            if request.remark:
                creator.remark = request.remark
            creator.status = request.status
            CreatorRepository.save(session, creator)
        creator_payload = creator.to_dict()

    response = {"creator": creator_payload, "created": created}
    if request.initial_sync:
        response["sync"] = sync_creator_videos(creator_payload["id"])
        response["creator"] = get_creator_detail(creator_payload["id"])
    return response


def list_creators() -> list[dict]:
    with session_scope() as session:
        creators = CreatorRepository.list_all(session)
        return [creator.to_dict() for creator in creators]


def get_creator_detail(creator_id: int) -> dict:
    with session_scope() as session:
        creator = CreatorRepository.get_by_id(session, creator_id)
        if creator is None:
            raise ValueError("博主不存在")
        payload = creator.to_dict()
        payload["video_count"] = len(creator.videos)
        return payload


def update_creator(creator_id: int, request: CreatorUpdateRequest) -> dict:
    with session_scope() as session:
        creator = CreatorRepository.get_by_id(session, creator_id)
        if creator is None:
            raise ValueError("博主不存在")

        if request.domain_tag is not None:
            creator.domain_tag = request.domain_tag
        if request.remark is not None:
            creator.remark = request.remark
        if request.status is not None:
            creator.status = request.status

        CreatorRepository.save(session, creator)
        return creator.to_dict()
