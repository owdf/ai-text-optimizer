"""Validation helpers for user-configured AI service URLs."""

import ipaddress
from urllib.parse import SplitResult, urlsplit


def _parse_http_url(url: str) -> SplitResult:
    value = str(url or "").strip()
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("API 地址必须使用 http:// 或 https://")
    if not parsed.hostname:
        raise ValueError("API 地址缺少主机名")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("API 地址不能包含用户名或密码")
    if parsed.query or parsed.fragment:
        raise ValueError("API 基础地址不能包含查询参数或片段")
    return parsed


def is_loopback_url(url: str) -> bool:
    """Return True only when the parsed hostname is an exact loopback host."""
    try:
        host = (_parse_http_url(url).hostname or "").rstrip(".").lower()
    except ValueError:
        return False

    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_api_base_url(url: str) -> str:
    """Validate and normalize an API base URL.

    Plain HTTP is restricted to exact loopback hosts so API keys and selected
    text cannot be sent unencrypted to a remote service.
    """
    value = str(url or "").strip().rstrip("/")
    parsed = _parse_http_url(value)
    if parsed.scheme.lower() == "http" and not is_loopback_url(value):
        raise ValueError("远程 API 地址必须使用 HTTPS")
    return value
