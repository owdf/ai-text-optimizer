"""
TextCleaner 模块单元测试
"""

from text_cleaner import clean_markdown, format_for_display


class TestTextCleaner:
    """TextCleaner 测试"""

    def test_clean_bold(self):
        """测试加粗清理"""
        assert clean_markdown("**bold text**") == "bold text"

    def test_clean_italic(self):
        """测试斜体清理"""
        assert clean_markdown("*italic text*") == "italic text"

    def test_clean_heading(self):
        """测试标题清理"""
        assert clean_markdown("# Heading 1") == "[Heading 1]"
        assert clean_markdown("## Heading 2") == "[Heading 2]"

    def test_clean_code_block(self):
        """测试代码块清理"""
        result = clean_markdown("```python\nprint('hello')\n```")
        assert "print('hello')" in result
        assert "```" not in result

    def test_clean_inline_code(self):
        """测试行内代码清理"""
        assert clean_markdown("use `code()` function") == "use code() function"

    def test_clean_link(self):
        """测试链接清理"""
        result = clean_markdown("[click here](https://example.com)")
        assert result == "click here"

    def test_clean_list(self):
        """测试列表清理"""
        result = clean_markdown("- Item 1\n- Item 2")
        assert "Item 1" in result
        assert "Item 2" in result

    def test_empty_input(self):
        """测试空输入"""
        assert clean_markdown("") == ""
        assert clean_markdown(None) is None

    def test_plain_text_passthrough(self):
        """测试纯文本直通"""
        text = "This is plain text without any markdown."
        result = clean_markdown(text)
        assert "plain text" in result

    def test_mixed_formatting(self):
        """测试混合格式"""
        text = "### Title\n\n**Bold** and *italic* with `code`"
        result = clean_markdown(text)
        assert "[Title]" in result
        assert "Bold" in result
        assert "italic" in result
        assert "code" in result

    def test_format_for_display(self):
        """测试显示格式化"""
        text = "**Hello**\r\n*World*"
        result = format_for_display(text)
        assert "\r\n" not in result
        assert "Hello" in result
        assert "World" in result

    def test_fenced_code_is_not_rewritten(self):
        text = "```python\n# keep this comment\nresult = a * b * c\n```"
        result = clean_markdown(text)
        assert "```" not in result
        assert "# keep this comment" in result
        assert "result = a * b * c" in result

    def test_direct_code_and_yaml_are_not_rewritten(self):
        code = "result = a * b * c\n# keep this comment"
        yaml = "items:\n  - one\n  - two"
        assert clean_markdown(code) == code
        assert clean_markdown(yaml) == yaml
