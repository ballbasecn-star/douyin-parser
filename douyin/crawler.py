"""
本地抖音爬虫 - 直接请求抖音 API（无需远程服务）

核心流程:
1. 从分享文本提取短链接
2. 重定向获取 aweme_id
3. 构造请求参数 + a_bogus 签名
4. 携带 Cookie 请求抖音 API
5. 解析视频数据
"""
import logging
import os
import re
from typing import Optional, Dict
from urllib.parse import urlencode, quote

import requests

from .abogus import ABogus
from .models import VideoInfo
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)

# ==================== 配置 ====================

POST_DETAIL_API = "https://www.douyin.com/aweme/v1/web/aweme/detail/"

# 必须与 abogus.py 中 ua_code 匹配的 User-Agent（ua_code 基于此 UA 生成）
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.212 Safari/537.36"
)

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Referer": "https://www.douyin.com/",
    "User-Agent": USER_AGENT,
}

# BaseRequestModel 的默认参数（精简自服务器 models.py）
BASE_PARAMS = {
    "device_platform": "webapp",
    "aid": "6383",
    "channel": "channel_pc_web",
    "pc_client_type": "1",
    "version_code": "290100",
    "version_name": "29.1.0",
    "cookie_enabled": "true",
    "screen_width": "1920",
    "screen_height": "1080",
    "browser_language": "zh-CN",
    "browser_platform": "Win32",
    "browser_name": "Chrome",
    "browser_version": "90.0.4430.212",
    "browser_online": "true",
    "engine_name": "Blink",
    "engine_version": "90.0.4430.212",
    "os_name": "Windows",
    "os_version": "10",
    "cpu_core_num": "12",
    "device_memory": "8",
    "platform": "PC",
    "downlink": "10",
    "effective_type": "4g",
    "round_trip_time": "0",
}

# 短链正则
SHORT_URL_PATTERN = re.compile(r"https?://v\.douyin\.com/[\w\-]+/?")
FULL_URL_PATTERN = re.compile(r"https?://(?:www\.)?douyin\.com/(?:video|note)/(\d+)")

# 移动端 UA（用于重定向解析）
MOBILE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
}


# ==================== 链接提取 ====================

def extract_share_link(text: str) -> Optional[str]:
    """从分享文本中提取抖音链接"""
    match = SHORT_URL_PATTERN.search(text)
    if match:
        link = match.group(0).rstrip("/") + "/"
        logger.info(f"提取到短链接: {link}")
        return link

    match = FULL_URL_PATTERN.search(text)
    if match:
        link = match.group(0)
        logger.info(f"提取到完整链接: {link}")
        return link

    return None


def extract_aweme_id(url: str) -> Optional[str]:
    """从 URL 中提取 aweme_id"""
    match = re.search(r"/video/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/note/(\d+)", url)
    if match:
        return match.group(1)
    # 尝试从 query 参数中提取
    match = re.search(r"aweme_id=(\d+)", url)
    if match:
        return match.group(1)
    return None


def resolve_short_url(short_url: str) -> Optional[str]:
    """
    解析短链接重定向，获取 aweme_id

    Returns:
        aweme_id 或 None
    """
    try:
        # 先用移动端 UA 获取重定向
        resp = requests.get(short_url, headers=MOBILE_HEADERS, allow_redirects=True, timeout=10)
        if resp.status_code == 200:
            final_url = resp.url
            logger.debug(f"重定向 → {final_url}")

            # 检查是否被重定向到首页
            if final_url.rstrip("/") in ("https://www.douyin.com", "https://m.douyin.com"):
                logger.warning("链接被重定向到首页，可能已失效")
                return None

            aweme_id = extract_aweme_id(final_url)
            if aweme_id:
                logger.info(f"获取到 aweme_id: {aweme_id}")
                return aweme_id

    except Exception as e:
        logger.error(f"解析短链接失败: {e}")

    return None


# ==================== API 请求 ====================

def gen_mstoken() -> str:
    """生成随机 msToken"""
    import random
    import string
    chars = string.ascii_letters + string.digits + "_-"
    return "".join(random.choice(chars) for _ in range(128))


def build_post_detail_params(aweme_id: str) -> dict:
    """构造作品详情 API 的请求参数"""
    params = dict(BASE_PARAMS)
    params["aweme_id"] = aweme_id
    params["msToken"] = ""
    return params


def sign_params(params: dict) -> str:
    """
    使用 a_bogus 签名参数，返回完整 URL

    Returns:
        签名后的完整 URL
    """
    bogus = ABogus()
    a_bogus = bogus.get_value(params, method="GET")
    url = f"{POST_DETAIL_API}?{urlencode(params)}&a_bogus={quote(a_bogus, safe='')}"
    return url


def fetch_video_detail(aweme_id: str, cookie: str = None) -> Optional[Dict]:
    """
    请求抖音 API 获取视频详情

    Args:
        aweme_id: 视频 ID
        cookie: 抖音 Cookie

    Returns:
        原始 API 响应 data，失败返回 None
    """
    # 构造参数并签名
    params = build_post_detail_params(aweme_id)
    signed_url = sign_params(params)

    # 构造请求头
    headers = dict(DEFAULT_HEADERS)
    if cookie:
        headers["Cookie"] = cookie

    logger.info(f"请求抖音 API: aweme_id={aweme_id}")
    logger.debug(f"URL: {signed_url[:100]}...")

    try:
        resp = requests.get(signed_url, headers=headers, timeout=30)

        if resp.status_code == 200:
            data = resp.json()

            # 检查返回数据
            if data.get("status_code") == 0:
                aweme_detail = data.get("aweme_detail")
                if aweme_detail:
                    logger.info("✅ 抖音 API 返回成功")
                    return aweme_detail
                else:
                    logger.warning(f"API 返回无 aweme_detail: {list(data.keys())}")
            else:
                logger.warning(f"API 状态码异常: {data.get('status_code')}, {data.get('status_msg', '')}")
        else:
            logger.warning(f"HTTP 错误: {resp.status_code}")

    except Exception as e:
        logger.error(f"请求抖音 API 失败: {e}")

    return None


# ==================== 数据解析 ====================

def parse_video_data(data: Dict) -> VideoInfo:
    """将抖音 API 返回的数据解析为 VideoInfo"""
    info = VideoInfo()

    try:
        info.video_id = str(data.get("aweme_id", ""))
        info.title = data.get("desc", "")
        info.description = data.get("desc", "")
        info.share_url = f"https://www.douyin.com/video/{info.video_id}" if info.video_id else ""
        info.create_time = data.get("create_time", 0)

        # 作者
        author = data.get("author", {}) or {}
        info.author = author.get("nickname", "")
        info.author_id = author.get("unique_id", "") or author.get("short_id", "")
        avatar = author.get("avatar_thumb", {})
        if avatar and isinstance(avatar, dict):
            url_list = avatar.get("url_list", [])
            if url_list:
                info.author_avatar = url_list[0]

        # 统计
        stats = data.get("statistics", {}) or {}
        info.play_count = stats.get("play_count", 0) or 0
        info.like_count = stats.get("digg_count", 0) or 0
        info.comment_count = stats.get("comment_count", 0) or 0
        info.share_count = stats.get("share_count", 0) or 0
        info.collect_count = stats.get("collect_count", 0) or 0

        # 封面
        video = data.get("video", {}) or {}
        cover = video.get("cover", {}) or data.get("cover", {})
        if cover and isinstance(cover, dict):
            url_list = cover.get("url_list", [])
            if url_list:
                info.cover_url = url_list[0]

        # 时长
        info.duration = video.get("duration", 0) or data.get("duration", 0) or 0

        # Hashtags
        text_extra = data.get("text_extra", [])
        if isinstance(text_extra, list):
            for extra in text_extra:
                if isinstance(extra, dict):
                    tag = extra.get("hashtag_name", "")
                    if tag:
                        info.hashtags.append(f"#{tag}")
        if not info.hashtags and info.description:
            tags = re.findall(r"#([^\s#]+)", info.description)
            info.hashtags = [f"#{t}" for t in tags[:10]]

    except Exception as e:
        logger.error(f"解析视频数据失败: {e}")

    return info


def get_video_download_url(data: Dict) -> Optional[str]:
    """从 API 数据中提取无水印视频下载链接"""
    try:
        video = data.get("video", {})
        # 尝试获取无水印链接
        play_addr = video.get("play_addr", {})
        if play_addr:
            url_list = play_addr.get("url_list", [])
            if url_list:
                # 替换为无水印域名
                url = url_list[0]
                url = url.replace("playwm", "play")
                return url
        # 降级: bit_rate
        bit_rate = video.get("bit_rate", [])
        if bit_rate:
            play_addr = bit_rate[0].get("play_addr", {})
            url_list = play_addr.get("url_list", [])
            if url_list:
                return url_list[0]
    except Exception as e:
        logger.error(f"提取下载链接失败: {e}")
    return None


# ==================== 主入口 ====================

def crawl_video(share_text: str) -> Optional[tuple]:
    """
    完整的本地爬取流程

    Args:
        share_text: 分享文本（包含抖音链接）

    Returns:
        (VideoInfo, raw_data) 元组，失败返回 None
    """
    # 1. 提取链接
    link = extract_share_link(share_text)
    if not link:
        logger.error("未找到抖音链接")
        return None

    # 2. 获取 aweme_id
    aweme_id = None

    # 如果是完整链接，直接提取
    aweme_id = extract_aweme_id(link)

    # 如果是短链接，需要重定向
    if not aweme_id:
        aweme_id = resolve_short_url(link)

    if not aweme_id:
        logger.error("无法获取 aweme_id")
        return None

    # 3. 获取 Cookie
    cm = get_cookie_manager()
    cookie = cm.get_cookie()
    if not cookie:
        logger.warning("⚠️ 未设置 Cookie，API 可能返回受限数据")
        logger.warning("   请运行: python main.py cookie set \"你的Cookie\"")

    # 4. 请求 API
    raw_data = fetch_video_detail(aweme_id, cookie)
    if not raw_data:
        logger.error("❌ 抖音 API 请求失败")
        return None

    # 5. 解析数据
    video_info = parse_video_data(raw_data)
    logger.info(f"✅ 解析成功: {video_info.title[:50]}")

    return video_info, raw_data
