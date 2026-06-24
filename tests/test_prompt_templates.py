"""
PromptTemplates 模块单元测试
"""

import json
import tempfile
from pathlib import Path
from prompt_templates import PromptTemplateManager, PromptTemplate


class TestPromptTemplates:
    """PromptTemplates 测试"""

    def test_builtin_templates_loaded(self):
        """测试内置模板已加载"""
        mgr = PromptTemplateManager()
        assert "code_fix" in mgr.templates
        assert "code_optimize" in mgr.templates
        assert "translate" in mgr.templates
        assert "summarize" in mgr.templates

    def test_get_template(self):
        """测试获取模板"""
        mgr = PromptTemplateManager()
        tpl = mgr.get_template("code_fix")
        assert tpl is not None
        assert "代码修复" in tpl.name or "Code Fix" in tpl.name

    def test_format_prompt(self):
        """测试格式化提示词"""
        mgr = PromptTemplateManager()
        result = mgr.format_prompt("code_fix", "print('hello')", source="VSCode", language="python")
        assert result is not None
        assert "print('hello')" in result
        assert "VSCode" in result
        assert "python" in result

    def test_format_prompt_invalid_key(self):
        """测试无效模板键"""
        mgr = PromptTemplateManager()
        result = mgr.format_prompt("nonexistent", "text")
        assert result is None

    def test_add_delete_template(self):
        """测试添加和删除模板"""
        mgr = PromptTemplateManager()
        success = mgr.add_template(
            "test_tpl",
            "Test Template",
            "A test",
            "Hello {text}",
            category="custom"
        )
        assert success
        assert "test_tpl" in mgr.templates

        # Delete
        success = mgr.delete_template("test_tpl")
        assert success
        assert "test_tpl" not in mgr.templates

    def test_cannot_delete_builtin(self):
        """测试不能删除内置模板"""
        mgr = PromptTemplateManager()
        success = mgr.delete_template("code_fix")
        assert not success
        assert "code_fix" in mgr.templates

    def test_cannot_override_builtin(self):
        """测试不能覆盖内置模板"""
        mgr = PromptTemplateManager()
        success = mgr.add_template("code_fix", "Override", "desc", "prompt")
        assert not success

    def test_update_template(self):
        """测试更新模板"""
        mgr = PromptTemplateManager()
        mgr.add_template("update_test", "Original", "desc", "prompt {text}")
        success = mgr.update_template("update_test", name="Updated", prompt="new prompt {text}")
        assert success

        tpl = mgr.get_template("update_test")
        assert tpl.name == "Updated"
        assert "new prompt" in tpl.prompt

        mgr.delete_template("update_test")

    def test_get_all_templates(self):
        """测试获取所有模板"""
        mgr = PromptTemplateManager()
        all_tpls = mgr.get_all_templates()
        assert len(all_tpls) >= 10  # at least 10 builtins

    def test_get_templates_by_category(self):
        """测试按分类获取模板"""
        mgr = PromptTemplateManager()
        cats = mgr.get_templates_by_category()
        assert "code" in cats
        assert "debug" in cats
        assert "general" in cats

    def test_format_prompt_missing_placeholder(self):
        """测试缺少占位符时的回退"""
        mgr = PromptTemplateManager()
        mgr.add_template(
            "no_placeholder_test",
            "Test",
            "desc",
            "This template has no placeholders",
            category="custom"
        )
        result = mgr.format_prompt("no_placeholder_test", "some text")
        assert result is not None
        assert "no placeholders" in result
        mgr.delete_template("no_placeholder_test")
