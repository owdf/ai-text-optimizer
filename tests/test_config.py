"""
Config 模块单元测试
"""

import json
import tempfile
from pathlib import Path
from config import Config


class TestConfig:
    """Config 测试"""

    def test_default_config(self):
        """测试默认配置创建"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            assert cfg.get("ai_service.provider") in ("openai", "openai_compatible")
            assert cfg.get("hotkey.trigger") == "ctrl+shift+q"
            assert cfg.get("ui.theme") == "dark"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_get_set(self):
        """测试配置的 get/set"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            cfg.set("ai_service.api_key", "test-key-123")
            assert cfg.get("ai_service.api_key") == "test-key-123"

            cfg.set("new.nested.key", "value")
            assert cfg.get("new.nested.key") == "value"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_get_default(self):
        """测试默认值"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            assert cfg.get("nonexistent.key") is None
            assert cfg.get("nonexistent.key", "fallback") == "fallback"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_get_hotkey(self):
        """测试热键获取"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            assert cfg.get_hotkey() == "ctrl+shift+q"

            cfg.set_hotkey("alt+x")
            assert cfg.get_hotkey() == "alt+x"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_save_load(self):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            cfg.set("ai_service.api_key", "saved-key")
            cfg.save()

            # 重新加载
            cfg2 = Config(tmp_path)
            assert cfg2.get("ai_service.api_key") == "saved-key"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_is_api_configured(self):
        """测试 API 配置检查"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            # 默认有 base_url 但没有 api_key
            assert not cfg.is_api_configured()

            cfg.set("ai_service.api_key", "test-key")
            assert cfg.is_api_configured()

            # 本地 Ollama 允许空 key
            cfg.set("ai_service.api_key", "")
            cfg.set("ai_service.base_url", "http://localhost:11434/v1")
            assert cfg.is_api_configured()

            # Hostname/query substrings must not impersonate a loopback service.
            cfg.set("ai_service.base_url", "https://localhost.evil.example/v1")
            assert not cfg.is_api_configured()
            cfg.set("ai_service.base_url", "https://evil.example/v1?next=127.0.0.1")
            assert not cfg.is_api_configured()

            # Plain HTTP is only permitted for exact loopback hosts.
            cfg.set("ai_service.api_key", "test-key")
            cfg.set("ai_service.base_url", "http://api.example.com/v1")
            assert not cfg.is_api_configured()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_extra_prompt(self):
        """测试 prompts.extra 读写"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            assert cfg.get_prompt("extra") in ("", None) or cfg.get_prompt("extra") == ""
            cfg.set_prompt("extra", "be concise")
            assert cfg.get_prompt("extra") == "be concise"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_reset_to_default(self):
        """测试重置"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            cfg = Config(tmp_path)
            cfg.set("ai_service.api_key", "modified-key")
            cfg.reset_to_default()
            assert cfg.get("ai_service.api_key") == ""
        finally:
            Path(tmp_path).unlink(missing_ok=True)
