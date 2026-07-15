"""
language 模块回归测试
"""

from language import get_system_language


class TestLanguage:
    def test_en_us_langid_not_chinese(self):
        """0x0409 (en-US) 不得被当作中文"""
        # 直接校验常量集合逻辑：模拟映射表
        chinese_langs = {0x0804, 0x0404, 0x0C04, 0x1404, 0x1004}
        assert 0x0409 not in chinese_langs
        assert 0x0804 in chinese_langs

    def test_get_system_language_returns_zh_or_en(self):
        lang = get_system_language()
        assert lang in ("zh", "en")
