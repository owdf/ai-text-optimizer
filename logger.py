"""
结构化日志模块
替代散落的 print() 调用，支持控制台和文件日志
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from app_paths import resolve_log_dir

# 默认日志格式
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_LOG_DATE_FORMAT = "%H:%M:%S"

# 日志文件路径（打包后位于持久化用户目录）
_LOG_DIR = resolve_log_dir(Path(__file__).parent)
_LOG_FILE = _LOG_DIR / "app.log"

# 全局 logger 缓存
_loggers: dict = {}
_initialized = False


def _init_logging(level: int = logging.INFO, log_to_file: bool = False) -> None:
    """初始化日志系统。

    默认只输出到控制台；文件日志由 enable_file_logging / 配置
    general.enable_logging 再开启。
    """
    global _initialized
    if _initialized:
        return

    root = logging.getLogger("ai_text_optimizer")
    root.setLevel(level)

    # 避免重复添加 handler
    if root.handlers:
        _initialized = True
        return

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
    root.addHandler(console)

    # 文件 handler（默认关闭，尊重 enable_logging=false）
    if log_to_file:
        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "%Y-%m-%d %H:%M:%S"
            ))
            root.addHandler(file_handler)
        except OSError:
            pass  # 文件日志不可用时静默跳过

    _initialized = True


def get_logger(name: str = "app") -> logging.Logger:
    """获取模块级 logger

    Args:
        name: logger 名称，会自动加上 'ai_text_optimizer.' 前缀

    Returns:
        logging.Logger 实例
    """
    _init_logging()

    full_name = f"ai_text_optimizer.{name}"
    if full_name not in _loggers:
        _loggers[full_name] = logging.getLogger(full_name)

    return _loggers[full_name]


def set_level(level: int) -> None:
    """动态设置日志级别"""
    _init_logging()
    logging.getLogger("ai_text_optimizer").setLevel(level)


def enable_file_logging(enabled: bool) -> None:
    """启用/禁用文件日志"""
    root = logging.getLogger("ai_text_optimizer")
    for handler in root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            root.removeHandler(handler)
            handler.close()

    if enabled:
        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "%Y-%m-%d %H:%M:%S"
            ))
            root.addHandler(file_handler)
        except OSError:
            pass
