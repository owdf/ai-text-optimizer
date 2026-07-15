"""
AI服务适配层
支持多种AI服务提供商，使用智能提示词系统

优化版本：
- 提取公共异常处理方法 _request_with_retry
- 减少重复的 try/except 代码块
- 添加请求重试机制
- 使用结构化日志模块
"""

import time
import requests
from typing import Dict, List, Optional, Any
from config import get_config
from context_analyzer import get_context_analyzer
from text_cleaner import clean_markdown
from url_utils import is_loopback_url, validate_api_base_url
from logger import get_logger

logger = get_logger("ai_service")

# 可重试的 HTTP 状态码
_RETRYABLE_STATUS = {429, 502, 503, 504}
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds


class AIServiceError(Exception):
    """AI服务异常"""
    pass


class AIService:
    """统一AI服务接口"""

    # API 格式：OpenAI / Anthropic（兼容旧值 openai_compatible / claude）
    API_FORMAT_OPENAI = "openai"
    API_FORMAT_ANTHROPIC = "anthropic"
    API_FORMAT_ALIASES = {
        "openai": API_FORMAT_OPENAI,
        "openai_compatible": API_FORMAT_OPENAI,
        "anthropic": API_FORMAT_ANTHROPIC,
        "claude": API_FORMAT_ANTHROPIC,
    }

    # 预设服务（可一键填入，填入后仍可手动改）
    PRESET_SERVICES = {
        "openai": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "provider": API_FORMAT_OPENAI,
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "provider": API_FORMAT_OPENAI,
        },
        "zhipu": {
            "name": "智谱AI (ChatGLM)",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4",
            "provider": API_FORMAT_OPENAI,
        },
        "moonshot": {
            "name": "月之暗面 (Kimi)",
            "base_url": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-8k",
            "provider": API_FORMAT_OPENAI,
        },
        "qwen": {
            "name": "阿里通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "provider": API_FORMAT_OPENAI,
        },
        "ollama": {
            "name": "本地 Ollama",
            "base_url": "http://localhost:11434/v1",
            "model": "llama3",
            "provider": API_FORMAT_OPENAI,
        },
        "anthropic": {
            "name": "Anthropic Claude",
            "base_url": "https://api.anthropic.com/v1",
            "model": "claude-sonnet-4-20250514",
            "provider": API_FORMAT_ANTHROPIC,
        },
        "custom": {
            "name": "Custom",
            "base_url": "",
            "model": "",
            "provider": API_FORMAT_OPENAI,
        },
    }

    @classmethod
    def normalize_provider(cls, provider: str) -> str:
        """将配置中的 provider 规范为 openai / anthropic"""
        key = (provider or cls.API_FORMAT_OPENAI).strip().lower()
        return cls.API_FORMAT_ALIASES.get(key, cls.API_FORMAT_OPENAI)

    def __init__(self):
        """初始化AI服务"""
        self.config = get_config()
        self.analyzer = get_context_analyzer()
        self._session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        api_key = self.config.get("ai_service.api_key", "")
        provider = self.normalize_provider(
            self.config.get("ai_service.provider", self.API_FORMAT_OPENAI)
        )

        if provider == self.API_FORMAT_ANTHROPIC:
            return {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _get_base_url(self) -> str:
        """获取API基础URL"""
        raw_url = self.config.get("ai_service.base_url", "https://api.openai.com/v1")
        try:
            return validate_api_base_url(raw_url)
        except ValueError as e:
            raise AIServiceError(str(e)) from e

    def _get_model(self) -> str:
        """获取模型名称"""
        return self.config.get("ai_service.model", "gpt-4")

    def _get_max_tokens(self) -> int:
        """获取最大token数"""
        return self.config.get("ai_service.max_tokens", 4000)

    def _get_temperature(self) -> float:
        """获取温度参数"""
        return self.config.get("ai_service.temperature", 0.7)

    # ---- 公共请求方法（消除重复异常处理）----

    def _make_request(self, url: str, payload: dict) -> dict:
        """
        发送HTTP请求：对 429/5xx 做有限次指数退避重试。

        Raises:
            AIServiceError: 请求失败时抛出异常
        """
        last_error: Optional[Exception] = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = self._session.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=120,
                )
                if response.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        f"可重试状态 {response.status_code}，{delay:.1f}s 后重试 "
                        f"({attempt + 1}/{_MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as e:
                raise AIServiceError(f"请求超时(120s): {e}") from e
            except requests.exceptions.HTTPError as e:
                last_error = e
                status = e.response.status_code if e.response is not None else None
                if status in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"HTTP {status}，{delay:.1f}s 后重试 ({attempt + 1}/{_MAX_RETRIES})")
                    time.sleep(delay)
                    continue
                raise AIServiceError(f"网络请求失败: {e}") from e
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < _MAX_RETRIES - 1:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"网络错误，{delay:.1f}s 后重试 ({attempt + 1}/{_MAX_RETRIES}): {e}")
                    time.sleep(delay)
                    continue
                raise AIServiceError(f"网络请求失败: {e}") from e
            except (ValueError, KeyError, IndexError, TypeError) as e:
                raise AIServiceError(f"响应格式错误: {e}") from e

        raise AIServiceError(f"网络请求失败: {last_error}")

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> str:
        """
        发送聊天请求（非流式）。

        Args:
            messages: 消息列表
            stream: 必须为 False；流式暂未实现

        Returns:
            AI响应内容

        Raises:
            AIServiceError: 请求失败或 stream=True 时抛出
        """
        if stream:
            raise AIServiceError("流式响应尚未实现，请使用 stream=False")

        api_key = self.config.get("ai_service.api_key", "")
        base_url = self._get_base_url()
        if not base_url:
            raise AIServiceError("未配置 API 地址 (base_url)")
        # 本地服务（如 Ollama）允许空 key
        is_local = is_loopback_url(base_url)
        if not api_key and not is_local:
            raise AIServiceError("未配置 API 密钥，请先在设置中填写")

        provider = self.normalize_provider(
            self.config.get("ai_service.provider", self.API_FORMAT_OPENAI)
        )

        if provider == self.API_FORMAT_OPENAI:
            return self._chat_openai_compatible(messages)
        if provider == self.API_FORMAT_ANTHROPIC:
            return self._chat_claude(messages)
        raise AIServiceError(f"不支持的 API 格式: {provider}（仅支持 OpenAI / Anthropic）")

    def _chat_openai_compatible(self, messages: List[Dict[str, str]]) -> str:
        """调用OpenAI兼容API（非流式）"""
        base_url = self._get_base_url().rstrip("/")
        url = f"{base_url}/chat/completions"

        payload = {
            "model": self._get_model(),
            "messages": messages,
            "max_tokens": self._get_max_tokens(),
            "temperature": self._get_temperature(),
        }

        result = self._make_request(url, payload)
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise AIServiceError(f"响应格式错误: {e}") from e

    def _chat_claude(self, messages: List[Dict[str, str]]) -> str:
        """调用Claude API（非流式）"""
        base_url = self._get_base_url().rstrip("/")
        url = f"{base_url}/messages"

        # 转换消息格式
        claude_messages = []
        system_message = None

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        payload = {
            "model": self._get_model(),
            "max_tokens": self._get_max_tokens(),
            "messages": claude_messages
        }

        if system_message:
            payload["system"] = system_message

        result = self._make_request(url, payload)
        try:
            return result["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise AIServiceError(f"响应格式错误: {e}") from e

    def analyze_and_optimize(self, text: str) -> Dict[str, Any]:
        """
        分析文本并使用AI优化

        Args:
            text: 要分析和优化的文本

        Returns:
            包含分析结果和AI响应的字典
        """
        # 1. 获取当前窗口上下文
        context = self.analyzer.get_active_window()

        # 2. 分析文本类型
        analysis = self.analyzer.analyze_text(text, context)

        # 3. 生成智能提示词
        smart_prompt = self.analyzer.generate_smart_prompt(text, analysis, context)

        # 4. 调用AI
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的技术助手，擅长分析错误、代码、日志和配置。
请用清晰、简洁的纯文本格式回答。
不要使用Markdown语法（不要用**加粗**、不要用```代码块```、不要用#标题、不要用- 列表）。
代码直接写出来，用缩进表示层级。
用数字编号（1. 2. 3.）来组织要点。"""
            },
            {
                "role": "user",
                "content": smart_prompt
            }
        ]

        ai_response = self.chat(messages)

        # 5. 清理Markdown格式（以防万一）
        ai_response = clean_markdown(ai_response)

        return {
            "context": context,
            "analysis": analysis,
            "prompt": smart_prompt,
            "response": ai_response
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接

        Returns:
            测试结果
        """
        try:
            messages = [{"role": "user", "content": "Hello, please respond with 'OK' to confirm the connection."}]
            response = self.chat(messages)
            return {
                "success": True,
                "message": "连接成功",
                "response": response[:100] + "..." if len(response) > 100 else response
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}"
            }

    @classmethod
    def get_preset_services(cls) -> Dict[str, Dict]:
        """获取预设服务列表"""
        return cls.PRESET_SERVICES

    @classmethod
    def get_preset_service(cls, service_id: str) -> Optional[Dict]:
        """获取指定预设服务"""
        return cls.PRESET_SERVICES.get(service_id)


# 全局AI服务实例
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取全局AI服务实例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def reload_ai_service() -> AIService:
    """重新加载AI服务，关闭旧 Session 避免连接泄漏"""
    global _ai_service
    if _ai_service is not None:
        try:
            _ai_service._session.close()
        except Exception:
            pass
    _ai_service = AIService()
    return _ai_service
