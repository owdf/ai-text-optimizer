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

import signal
import threading
import traceback
from queue import Empty, Queue
import pyperclip
import customtkinter as ctk
from config import get_config
from ai_service import get_ai_service, AIServiceError
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
        # 用户从模板窗口手动选择后锁定；否则按内容类型自动选模板
        self._template_locked = False

        # 主窗口隐藏，以托盘形式运行；所有弹窗必须挂在此 root 上
        self.root = ctk.CTk()
        self.root.title(t("app_name"))
        self.root.geometry("1x1+0+0")
        self.root.withdraw()

        self.floating_window = get_floating_window(master=self.root)
        self.tray_icon = get_tray_icon()

        self._setup_callbacks()
        self.hotkey_listener = None
        self._processing = False
        self._processing_lock = threading.Lock()
        self._ui_queue = Queue()
        self._shutting_down = False

    # content_type → 默认模板
    _CONTENT_TEMPLATE_MAP = {
        "error": "code_fix",
        "code": "code_optimize",
        "log": "log_analyze",
        "config": "config_fix",
        "plain": "summarize",
    }

    def _setup_callbacks(self):
        self.floating_window.set_on_copy(self._copy_to_clipboard)
        self.tray_icon.set_on_settings(self._show_settings)
        self.tray_icon.set_on_hotkey_settings(self._show_hotkey_settings)
        self.tray_icon.set_on_templates(self._show_templates)
        self.tray_icon.set_on_quit(self._request_quit)
        self.tray_icon.set_on_toggle_hotkey(self._request_toggle_hotkey)
        self.tray_icon.set_on_change_lang(self._request_language_change)

    def _post_to_ui(self, callback, *args):
        """Thread-safe handoff to the Tk main thread."""
        if not self._shutting_down:
            self._ui_queue.put((callback, args))

    def _drain_ui_queue(self):
        """Run queued UI callbacks from the Tk main thread."""
        while True:
            try:
                callback, args = self._ui_queue.get_nowait()
            except Empty:
                break
            try:
                callback(*args)
            except Exception:
                logger.error(f"UI 回调失败:\n{traceback.format_exc()}")
            if self._shutting_down:
                break

        if not self._shutting_down:
            self.root.after(25, self._drain_ui_queue)

    def _copy_to_clipboard(self, text: str):
        pyperclip.copy(text)

    def _show_settings(self):
        self._post_to_ui(self._show_settings_thread)

    def _show_settings_thread(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(
                master=self.root, dispatcher=self._post_to_ui
            )
            self.settings_window.set_on_close(lambda: setattr(self, 'settings_window', None))
            self.settings_window.set_on_save(self._on_settings_save)
        self.settings_window.show()

    def _show_hotkey_settings(self):
        self._post_to_ui(self._show_hotkey_thread)

    def _show_hotkey_thread(self):
        # 暂停主热键监听，避免跟 HotkeyWindow 的 pynput 监听器冲突
        self._hotkey_was_running = (
            self.hotkey_listener is not None and self.hotkey_listener.is_running()
        )
        if self._hotkey_was_running:
            self.hotkey_listener.stop()

        if self.hotkey_window is None:
            self.hotkey_window = get_hotkey_window(
                master=self.root, dispatcher=self._post_to_ui
            )
            self.hotkey_window.set_on_close(self._on_hotkey_window_close)
            self.hotkey_window.set_on_save(self._on_hotkey_save)
        self.hotkey_window.show()

    def _on_hotkey_window_close(self):
        """HotkeyWindow 关闭时恢复主热键监听"""
        self.hotkey_window = None
        if self._hotkey_was_running and self.hotkey_listener:
            self.hotkey_listener.start()

    def _show_templates(self):
        self._post_to_ui(self._show_templates_thread)

    def _show_templates_thread(self):
        if self.template_window is None:
            self.template_window = get_template_window(master=self.root)
            self.template_window.set_on_close(lambda: setattr(self, 'template_window', None))
            self.template_window.set_on_select(self._on_template_select)
        self.template_window.show()

    def _on_template_select(self, template_key: str):
        self._current_template = template_key
        self._template_locked = True
        template = self.template_mgr.get_template(template_key)
        if template:
            logger.info(f"选择模板(已锁定): {template.name}")

    def _on_hotkey_save(self, new_hotkey: str):
        logger.info(f"热键已更新: {new_hotkey}")
        if self.hotkey_listener:
            self.hotkey_listener.update_hotkey(new_hotkey)
        self.tray_icon.update_hotkey_display()
        self.config = get_config()

    def _on_settings_save(self):
        self.config = get_config()
        # AIService reads the shared Config object for every request; retaining
        # the Session avoids closing an in-flight call during a settings save.
        self.ai_service = get_ai_service()
        if self.hotkey_listener:
            self.hotkey_listener.update_hotkey(self.config.get_hotkey())
        self.tray_icon.update_hotkey_display()
        # 同步文件日志开关
        from logger import enable_file_logging
        enable_file_logging(bool(self.config.get("general.enable_logging", False)))

    def _on_language_change(self, lang: str):
        """语言切换回调"""
        logger.info(f"语言切换: {lang}")
        self.tray_icon.update_language()

    def _request_language_change(self, lang: str):
        self._post_to_ui(self._on_language_change, lang)

    def _request_toggle_hotkey(self, enabled: bool):
        self._post_to_ui(self._toggle_hotkey, enabled)

    def _toggle_hotkey(self, enabled: bool):
        if self.hotkey_listener:
            if enabled:
                self.hotkey_listener.start()
            else:
                self.hotkey_listener.stop()
        self.tray_icon.set_hotkey_enabled(enabled)
        self.config.set("hotkey.enabled", bool(enabled))
        if not self.config.save():
            logger.warning("热键启用状态保存失败")

    def _on_hotkey_triggered(self):
        # 立即 CAS 置位，避免连按并发（必须在调度 after 之前）
        with self._processing_lock:
            if self._processing:
                logger.info("已有任务进行中，忽略热键")
                return
            self._processing = True

        logger.info("热键触发")
        # 等修饰键（Alt/Ctrl/Shift）释放后再模拟 Ctrl+C，
        # 否则 Alt+A 触发时立刻发 Ctrl+C 会变成 Ctrl+Alt+C 并抢焦点失败
        self._post_to_ui(self._schedule_text_capture)

    def _schedule_text_capture(self):
        self.root.after(180, self._start_text_capture)

    def _start_text_capture(self):
        """在后台抓取选区/剪贴板，结果回到主线程处理"""
        def worker():
            text = ""
            try:
                selected = self.text_selector.get_selection()
                if selected and str(selected).strip():
                    text = selected
            except Exception as e:
                logger.warning(f"选区获取失败: {e}")

            if text and str(text).strip():
                logger.info(f"获取到文本: {len(text)} 字符")
                self._post_to_ui(self._process_text, text)
            else:
                logger.info("未获取到文本")
                with self._processing_lock:
                    self._processing = False
                self._post_to_ui(self._show_no_text)

        threading.Thread(target=worker, daemon=True).start()

    def _show_no_text(self):
        self.floating_window.show(
            t("no_text"),
            t("no_text_msg"),
            {"app_name": "System", "app_category": "other", "content_type": "plain", "language": ""}
        )

    def _show_api_not_configured(self):
        self.floating_window.show(
            t("api_not_configured"),
            t("api_not_configured_msg"),
            {"app_name": "System", "app_category": "other", "content_type": "plain", "language": ""}
        )

    def _resolve_template_key(self, content_type: str) -> str:
        """用户锁定模板优先，否则按内容类型自动映射。"""
        if self._template_locked and self.template_mgr.get_template(self._current_template):
            return self._current_template
        mapped = self._CONTENT_TEMPLATE_MAP.get(content_type, "summarize")
        if self.template_mgr.get_template(mapped):
            return mapped
        return self._current_template

    def _process_text(self, text: str):
        logger.info("开始处理文本")

        if not self.config.is_api_configured():
            logger.warning("API 未配置")
            with self._processing_lock:
                self._processing = False
            self._show_api_not_configured()
            return

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
            template_key = self._resolve_template_key(analysis.content_type)
            logger.info(f"使用模板: {template_key} (locked={self._template_locked})")

            prompt = self.template_mgr.format_prompt(
                template_key,
                text,
                source=source,
                language=language
            )

            extra = (self.config.get_prompt("extra") or "").strip()
            if not prompt:
                # 模板缺失时回退智能提示词
                smart = self.context_analyzer.generate_smart_prompt(text, analysis, context)
                prompt = f"{smart}\n\n额外指令:\n{extra}" if extra else smart
            elif extra:
                prompt = f"{prompt}\n\n额外指令:\n{extra}"

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个专业的技术助手。请用纯文本回答，不要使用Markdown格式。"
                        "不要重复用户发送的原文内容，只输出你的分析和建议。"
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = clean_markdown(self.ai_service.chat(messages))
            result = {
                "context": context,
                "analysis": analysis,
                "response": response,
            }

            logger.info("AI调用完成")
            self._post_to_ui(self._update_result, result)

        except AIServiceError as e:
            error_msg = f"{t('ai_error')}: {str(e)}"
            logger.error(error_msg)
            self._post_to_ui(self._update_error, error_msg)
        except Exception as e:
            error_msg = f"{t('error')}: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self._post_to_ui(self._update_error, error_msg)
        finally:
            with self._processing_lock:
                self._processing = False

    def _update_result(self, result: dict):
        response = result.get("response", "No response")
        self.floating_window.update_result(response)

    def _update_error(self, error_msg: str):
        self.floating_window.update_result(error_msg)

    def _request_quit(self):
        self._post_to_ui(self._quit)

    def _quit(self):
        if self._shutting_down:
            return
        self._shutting_down = True
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

    def run(self):
        hotkey = self.config.get_hotkey()
        template = self.template_mgr.get_template(self._current_template)
        template_name = (
            f"{template.name} (auto)" if not self._template_locked and template
            else (template.name if template else "Default")
        )

        # 注册信号处理实现优雅退出
        def _signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在退出...")
            self._request_quit()

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
        hotkey_enabled = bool(self.config.get("hotkey.enabled", True))
        self.tray_icon.set_hotkey_enabled(hotkey_enabled)
        if hotkey_enabled:
            self.hotkey_listener.start()

        # 主循环启动后再提示：托盘就绪 / 未配置则弹出设置
        self.root.after(0, self._drain_ui_queue)
        self.root.after(600, self._on_app_ready)

        self.root.mainloop()

    def _on_app_ready(self):
        """启动后可见反馈：托盘通知 + 必要时打开设置窗口"""
        hotkey = self.config.get_hotkey().upper().replace("+", " + ")
        try:
            self.tray_icon.notify(
                t("app_name"),
                f"{t('start_ready')} · {t('start_hotkey')}: {hotkey}\n"
                f"{t('start_change_tip')}",
            )
        except Exception:
            pass

        logger.info(f"托盘已就绪，请查看系统托盘图标（可能在 ^ 折叠区）")

        # 未配置 API 时自动打开设置，避免「只有日志没有界面」
        if not self.config.is_api_configured():
            logger.info("API 未配置，自动打开设置窗口")
            self._show_settings()
        else:
            # 已配置时弹出一次就绪提示窗，证明 UI 可用
            self.floating_window.show(
                t("start_ready"),
                f"{t('start_hotkey')}: {hotkey}\n\n"
                f"{t('start_step1')}\n{t('start_step2')}\n"
                f"{t('start_step3')}\n\n"
                f"{t('start_change_tip')}",
                {
                    "app_name": t("app_name"),
                    "app_category": "other",
                    "content_type": "plain",
                    "language": "",
                },
            )


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # 按配置决定是否写文件日志（默认关闭）
    from config import get_config as _get_config
    from logger import enable_file_logging
    enable_file_logging(bool(_get_config().get("general.enable_logging", False)))

    app = AITextOptimizer()
    app.run()


if __name__ == "__main__":
    main()
