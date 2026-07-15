"""
PromptTemplates 模块单元测试
"""

import tempfile
from pathlib import Path
from prompt_templates import PromptTemplateManager, PromptTemplate


def _temp_mgr():
    """使用临时路径，避免污染项目 prompt_templates.json"""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink(missing_ok=True)  # 让 manager 从空文件开始
    return PromptTemplateManager(str(path)), path


class TestPromptTemplates:
    """PromptTemplates 测试"""

    def test_builtin_templates_loaded(self):
        """测试内置模板已加载"""
        mgr, path = _temp_mgr()
        try:
            assert "code_fix" in mgr.templates
            assert "code_optimize" in mgr.templates
            assert "translate" in mgr.templates
            assert "summarize" in mgr.templates
        finally:
            path.unlink(missing_ok=True)

    def test_get_template(self):
        """测试获取模板"""
        mgr, path = _temp_mgr()
        try:
            tpl = mgr.get_template("code_fix")
            assert tpl is not None
            assert "代码修复" in tpl.name or "Code Fix" in tpl.name
        finally:
            path.unlink(missing_ok=True)

    def test_format_prompt(self):
        """测试格式化提示词"""
        mgr, path = _temp_mgr()
        try:
            result = mgr.format_prompt(
                "code_fix", "print('hello')", source="VSCode", language="python"
            )
            assert result is not None
            assert "print('hello')" in result
            assert "VSCode" in result
            assert "python" in result
        finally:
            path.unlink(missing_ok=True)

    def test_format_prompt_invalid_key(self):
        """测试无效模板键"""
        mgr, path = _temp_mgr()
        try:
            result = mgr.format_prompt("nonexistent", "text")
            assert result is None
        finally:
            path.unlink(missing_ok=True)

    def test_add_delete_template(self):
        """测试添加和删除模板"""
        mgr, path = _temp_mgr()
        try:
            success = mgr.add_template(
                "test_tpl",
                "Test Template",
                "A test",
                "Hello {text}",
                category="custom",
            )
            assert success
            assert "test_tpl" in mgr.templates

            success = mgr.delete_template("test_tpl")
            assert success
            assert "test_tpl" not in mgr.templates
        finally:
            path.unlink(missing_ok=True)

    def test_cannot_delete_builtin(self):
        """测试不能删除内置模板"""
        mgr, path = _temp_mgr()
        try:
            success = mgr.delete_template("code_fix")
            assert not success
            assert "code_fix" in mgr.templates
        finally:
            path.unlink(missing_ok=True)

    def test_cannot_override_builtin(self):
        """测试不能覆盖内置模板"""
        mgr, path = _temp_mgr()
        try:
            success = mgr.add_template("code_fix", "Override", "desc", "prompt")
            assert not success
        finally:
            path.unlink(missing_ok=True)

    def test_update_template(self):
        """测试更新模板"""
        mgr, path = _temp_mgr()
        try:
            mgr.add_template("update_test", "Original", "desc", "prompt {text}")
            success = mgr.update_template(
                "update_test", name="Updated", prompt="new prompt {text}"
            )
            assert success

            tpl = mgr.get_template("update_test")
            assert tpl.name == "Updated"
            assert "new prompt" in tpl.prompt

            mgr.delete_template("update_test")
        finally:
            path.unlink(missing_ok=True)

    def test_get_all_templates(self):
        """测试获取所有模板"""
        mgr, path = _temp_mgr()
        try:
            all_tpls = mgr.get_all_templates()
            assert len(all_tpls) >= 10
        finally:
            path.unlink(missing_ok=True)

    def test_get_templates_by_category(self):
        """测试按分类获取模板"""
        mgr, path = _temp_mgr()
        try:
            cats = mgr.get_templates_by_category()
            assert "code" in cats
            assert "debug" in cats
            assert "general" in cats
        finally:
            path.unlink(missing_ok=True)

    def test_format_prompt_missing_placeholder(self):
        """测试缺少占位符时的回退"""
        mgr, path = _temp_mgr()
        try:
            mgr.add_template(
                "no_placeholder_test",
                "Test",
                "desc",
                "This template has no placeholders",
                category="custom",
            )
            result = mgr.format_prompt("no_placeholder_test", "some text")
            assert result is not None
            assert "no placeholders" in result
            mgr.delete_template("no_placeholder_test")
        finally:
            path.unlink(missing_ok=True)

    def test_format_prompt_preserves_literal_braces(self):
        """JSON/code braces are content, not positional format fields."""
        mgr, path = _temp_mgr()
        try:
            mgr.add_template(
                "literal_braces",
                "Literal braces",
                "desc",
                'Return JSON {} and {"ok": true} for {text}',
            )
            result = mgr.format_prompt("literal_braces", "input {source}")
            assert result == 'Return JSON {} and {"ok": true} for input {source}'
        finally:
            path.unlink(missing_ok=True)
