"""
ContextAnalyzer 回归测试
"""

from context_analyzer import ContextAnalyzer, WindowContext


def _ctx(category: str = "editor") -> WindowContext:
    return WindowContext(
        app_name="VS Code",
        window_title="test.py - VS Code",
        process_name="code",
        category=category,
    )


class TestContextAnalyzer:
    def test_brace_paren_regex_multi_char(self):
        """花括号/圆括号正则应匹配多字符内容"""
        assert ContextAnalyzer._RE_BRACES.search("{ return 1; }")
        assert ContextAnalyzer._RE_PARENS.search("(foo, bar)")
        assert ContextAnalyzer._RE_BRACES.search("{a}")
        assert ContextAnalyzer._RE_PARENS.search("(x)")

    def test_code_score_with_blocks(self):
        analyzer = ContextAnalyzer()
        text = "def hello():\n    return {\"ok\": True}\nprint(foo(bar))"
        score = analyzer._calculate_code_score(text, text.lower(), _ctx("editor"))
        assert score >= 0.3

    def test_error_content_type(self):
        analyzer = ContextAnalyzer()
        text = "Traceback (most recent call last):\n  File \"a.py\", line 1\nValueError: bad"
        analysis = analyzer.analyze_text(text, _ctx("terminal"))
        assert analysis.content_type == "error"
