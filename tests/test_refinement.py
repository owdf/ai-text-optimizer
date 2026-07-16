import threading
from types import SimpleNamespace

import pytest

from main import AITextOptimizer, build_refinement_prompt
from privacy_shield import PrivacyShield


@pytest.mark.parametrize("action", ["shorter", "clearer", "actionable"])
def test_refinement_prompt_contains_source_text(action):
    prompt = build_refinement_prompt(action, "Keep port 443 open")
    assert "Keep port 443 open" in prompt
    assert "Return only" in prompt


def test_refinement_prompt_rejects_unknown_action():
    with pytest.raises(ValueError):
        build_refinement_prompt("invent", "text")


def test_outbound_protection_can_be_disabled_explicitly():
    class ConfigStub:
        @staticmethod
        def get(key, default=None):
            return False if key == "privacy.enabled" else default

    app = AITextOptimizer.__new__(AITextOptimizer)
    app.config = ConfigStub()
    app.privacy_shield = PrivacyShield()
    source = "email me at dev@example.com"

    result = app._protect_outbound(source)

    assert result.protected_text == source
    assert result.total == 0


def test_initial_ai_call_redacts_network_payload_and_restores_local_result():
    class ConfigStub:
        @staticmethod
        def get(key, default=None):
            return True if key == "privacy.enabled" else default

        @staticmethod
        def get_prompt(_key):
            return ""

    class TemplateStub:
        @staticmethod
        def format_prompt(_key, text, **_kwargs):
            return f"Please process: {text}"

    sent = []

    class ServiceStub:
        @staticmethod
        def chat(messages):
            sent.extend(messages)
            return "Contact __ATO_EMAIL_1__ now"

    app = AITextOptimizer.__new__(AITextOptimizer)
    app.config = ConfigStub()
    app.privacy_shield = PrivacyShield()
    app.template_mgr = TemplateStub()
    app.ai_service = ServiceStub()
    app._template_locked = False
    app._current_template = "summarize"
    app._resolve_template_key = lambda _content_type: "summarize"
    app._processing_lock = threading.Lock()
    app._processing = True
    results = []
    app._post_to_ui = lambda callback, result: results.append(result)
    app._update_result = lambda result: None

    context = SimpleNamespace(app_name="Mail", category="messaging")
    analysis = SimpleNamespace(content_type="plain", language="en")
    app._call_ai("Email dev@example.com", context, analysis)

    assert "dev@example.com" not in sent[1]["content"]
    assert "__ATO_EMAIL_1__" in sent[1]["content"]
    assert results[0]["response"] == "Contact dev@example.com now"
    assert results[0]["protection_count"] == 1
    assert app._processing is False
