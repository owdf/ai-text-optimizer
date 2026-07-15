"""Security checks for custom API base URLs."""

import pytest

from url_utils import is_loopback_url, validate_api_base_url


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434/v1",
        "http://127.0.0.1:11434/v1",
        "http://[::1]:11434/v1",
    ],
)
def test_exact_loopback_urls(url):
    assert is_loopback_url(url)
    assert validate_api_base_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost.evil.example/v1",
        "https://evil.example/v1?next=127.0.0.1",
        "https://127.0.0.1.evil.example/v1",
    ],
)
def test_loopback_substrings_are_not_local(url):
    assert not is_loopback_url(url)


def test_remote_http_is_rejected():
    with pytest.raises(ValueError, match="HTTPS"):
        validate_api_base_url("http://api.example.com/v1")


def test_remote_https_is_normalized():
    assert validate_api_base_url(" https://api.example.com/v1/ ") == (
        "https://api.example.com/v1"
    )
