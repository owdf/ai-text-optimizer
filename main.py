"""
AI文本优化器 - 主程序
支持多语言

优化版本：
- 修复裸except子句为具体异常类型
- 将延迟导入移到文件顶部
- 改进错误日志记录
- 添加优雅退出信号处理
- 使用结构化日志模块
"""

import sys
import signal
import threading
import traceback
import pyperclip
import customtkinter as ctk
from config import get_config
from ai_service import get_ai_service, reload_ai_service, AIServiceError
from prompt_templates import get_template_manager
from clipboard import get_text_selector
from context_analyzer import get_context_analyzer
from hotkey import get_hotkey_listener, stop_hotkey_listener
from language import t, get_lang_manager
from text_cleaner import clean_markdown  # [优化] 移到顶部，避免运行时导入
from ui import (
    get_floating_window, SettingsWindow, get_tray_icon, stop_tray_icon,
    get_hotkey_window, get_template_window
)
from logger import get_logger

logger = get_logger("main")


class AITextOptimizer:
    """AI文本优化器"""

    def __init__(self):
        self.config = get_config()
        self.ai_service = get_ai_service()
        self.text_selector = get_text_selector()
        self.context_analyzer = get_context_analyzer()
        self.template_mgr = get_template_manager()
        self.lang_mgr = get_lang_manager()

        self.settings_window = None
        self.hotkey_window = None
        self.template_window = None

        self._current_template = "code_fix"

        self.root = ctk.CTk()
        self.root.withdraw()

        self.floating_window = get_floating_window()
        self.tray_icon = get_tray_icon()

        self._setup_callbacks()
        self.hotkey_listener = None
        self._processing = False

    def _setup_callbacks(self):
        self.floating_window.set_on_copy(self._copy_to_clipboard)
        self.tray_icon.set_on_settings(self._show_settings)
        self.tray_icon.set_on_hotkey_settings(self._show_hotkey_settings)
        self.tray_icon.set_on_templates(self._show_templates)
        self.tray_icon.set_on_quit(self._quit)
        self.tray_icon.set_on_toggle_hotkey(self._toggle_hotkey)
        self.tray_icon.set_on_change_lang(self._on_language_change)

    def _copy_to_clipboard(self, text: str):
        pyperclip.copy(text)

    def _show_settings(self):
        self.root.after(0, self._show_settings_thread)

    def _show_settings_thread(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow()
            self.settings_window.set_on_close(lambda: setattr(self, 'settings_window', None))
            self.settings_window.set_on_save(self._on_settings_save)
        self.settings_window.show()

    def _show_hotkey_settings(self):
        self.root.after(0, self._show_hotkey_thread)

    def _show_hotkey_thread(self):
        # 暂停主热键监听，避免跟 HotkeyWindow 的 pynput 监听器冲突
        self._hotkey_was_running = (
            self.hotkey_listener is not None and self.hotkey_listener.is_running()
        )
        if self._hotkey_was_running:
            self.hotkey_listener.stop()

        if self.hotkey_window is None:
            self.hotkey_window = get_hotkey_window()
            self.hotkey_window.set_on_close(self._on_hotkey_window_close)
            self.hotkey_window.set_on_save(self._on_hotkey_save)
        self.hotkey_window.show()

    def _on_hotkey_window_close(self):
        """HotkeyWindow 关闭时恢复主热键监听"""
        self.hotkey_window = None
        if self._hotkey_was_running and self.hotkey_listener:
            self.hotkey_listener.start()

    def _show_templates(self):
        self.root.after(0, self._show_templates_thread)

    def _show_templates_thread(self):
        if self.template_window is None:
            self.template_window = get_template_window()
            self.template_window.set_on_close(lambda: setattr(self, 'template_window', None))
            self.template_window.set_on_select(self._on_template_select)
        self.template_window.show()

    def _on_template_select(self, template_key: str):
        self._current_template = template_key
        template = self.template_mgr.get_template(template_key)
        if template:
            logger.info(f"选择模板: {template.name}")

    def _on_hotkey_save(self, new_hotkey: str):
        logger.info(f"热键已更新: {new_hotkey}")
        if self.hotkey_listener:
            self.hotkey_listener.update_hotkey(new_hotkey)
        self.tray_icon.update_hotkey_display()
        self.config = get_config()

    def _on_settings_save(self):
        self.config = get_config()
        self.ai_service = reload_ai_service()
        if self.hotkey_listener:
            self.hotkey_listener.update_hotkey(self.config.get_hotkey())
        self.tray_icon.update_hotkey_display()

    def _on_language_change(self, lang: str):
        """语言切换回调"""
        logger.info(f"语言切换: {lang}")
        self.tray_icon.update_language()

    def _toggle_hotkey(self, enabled: bool):
        if self.hotkey_listener:
            if enabled:
                self.hotkey_listener.start()
            else:
                self.hotkey_listener.stop()
            self.tray_icon.set_hotkey_enabled(enabled)

    def _on_hotkey_triggered(self):
        if self._processing:
            return

        logger.info("热键触发")

        # [优化] 使用具体异常类型替代裸except
        try:
            text = pyperclip.paste()
        except (pyperclip.PyperclipException, OSError, RuntimeError) as e:
            logger.warning(f"剪贴板读取失败: {e}")
            text = ""

        if text and text.strip():
            logger.info(f"获取到文本: {len(text)} 字符")
            self.root.after(0, self._process_text, text)
        else:
            logger.info("剪贴板为空")
            self.root.after(0, self._show_no_text)

    def _show_no_text(self):
        self.floating_window.show(
            t("no_text"),
            t("no_text_msg"),
            {"app_name": "System", "app_category": "other", "content_type": "plain", "language": ""}
        )

    def _process_text(self, text: str):
        logger.info("开始处理文本")
        self._processing = True

        context = self.context_analyzer.get_active_window()
        analysis = self.context_analyzer.analyze_text(text, context)

        logger.info(f"应用: {context.app_name}, 类型: {analysis.content_type}")

        context_info = {
            "app_name": context.app_name,
            "app_category": context.category,
            "content_type": analysis.content_type,
            "language": analysis.language,
        }
        self.floating_window.show(text, t("analyzing"), context_info)

        threading.Thread(target=self._call_ai, args=(text, context, analysis), daemon=True).start()

    def _call_ai(self, text: str, context, analysis):
        logger.info("调用AI...")
        try:
            source = f"{context.app_name} ({context.category})"
            language = analysis.language if analysis.language != "unknown" else ""

            prompt = self.template_mgr.format_prompt(
                self._current_template,
                text,
                source=source,
                language=language
            )

            if not prompt:
                result = self.ai_service.analyze_and_optimize(text)
            else:
                messages = [
                    {"role": "system", "content": "你是一个专业的技术助手。请用纯文本回答，不要使用Markdown格式。不要重复用户发送的原文内容，只输出你的分析和建议。"},
                    {"role": "user", "content": prompt}
                ]
                response = self.ai_service.chat(messages)
                # [优化] 不再需要延迟导入，clean_markdown已在顶部导入
                response = clean_markdown(response)

                result = {
                    "context": context,
                    "analysis": analysis,
                    "response": response
                }

            logger.info("AI调用完成")
            self.root.after(0, self._update_result, result)

        except AIServiceError as e:
            error_msg = f"{t('ai_error')}: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, self._update_error, error_msg)
        except Exception as e:
            error_msg = f"{t('error')}: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.root.after(0, self._update_error, error_msg)
        finally:
            self._processing = False

    def _update_result(self, result: dict):
        response = result.get("response", "No response")
        self.floating_window.update_result(response)

    def _update_error(self, error_msg: str):
        self.floating_window.update_result(error_msg)

    def _quit(self):
        logger.info("程序退出")
        stop_hotkey_listener()
        stop_tray_icon()
        if self.settings_window:
            self.settings_window.close()
        if self.hotkey_window:
            self.hotkey_window.close()
        if self.template_window:
            self.template_window.close()
        self.floating_window.close()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        hotkey = self.config.get_hotkey()
        template = self.template_mgr.get_template(self._current_template)
        template_name = template.name if template else "Default"

        # 注册信号处理实现优雅退出
        def _signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在退出...")
            self.root.after(0, self._quit)

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        logger.info("=" * 50)
        logger.info(f"  {t('start_title')}")
        logger.info("=" * 50)
        logger.info(f"  {t('start_hotkey')}: {hotkey.upper().replace('+', ' + ')}")
        logger.info(f"  {t('start_template')}: {template_name}")
        logger.info(f"  {t('start_usage')}:")
        logger.info(f"  {t('start_step1')}")
        logger.info(f"  {t('start_step2')}")
        logger.info(f"  {t('start_step3')}")
        logger.info(f"  {t('start_step4')}")
        logger.info(f"  {t('start_ready')}")

        self.tray_icon.start()

        self.hotkey_listener = get_hotkey_listener(self._on_hotkey_triggered)
        self.hotkey_listener.start()

        self.root.mainloop()


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = AITextOptimizer()
    app.run()


if __name__ == "__main__":
    main()
