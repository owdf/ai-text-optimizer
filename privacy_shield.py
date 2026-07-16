"""Local sensitive-data protection for prompts sent to AI providers.

The shield intentionally focuses on high-confidence credential and identity
patterns.  Replacements happen before the network request and are restored
only in the local response shown to the user.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Match, Optional, Pattern, Tuple


@dataclass(frozen=True)
class ProtectionSummary:
    """Result of protecting one outbound prompt."""

    protected_text: str
    replacements: Dict[str, str]
    counts: Dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def restore(self, text: str) -> str:
        """Restore placeholders that survived the model response unchanged."""
        restored = text
        for placeholder, original in self.replacements.items():
            restored = restored.replace(placeholder, original)
        return restored


@dataclass(frozen=True)
class _Rule:
    kind: str
    pattern: Pattern[str]
    group: Optional[str] = None


class PrivacyShield:
    """Redact secrets and personal identifiers without any network access."""

    _RULES: Tuple[_Rule, ...] = (
        _Rule(
            "private_key",
            re.compile(
                r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
                r"[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
                re.IGNORECASE,
            ),
        ),
        _Rule(
            "authorization",
            re.compile(
                r"(?P<prefix>\bAuthorization\s*:\s*(?:Bearer|Basic)\s+)"
                r"(?P<secret>[^\s,;]+)",
                re.IGNORECASE,
            ),
            "secret",
        ),
        _Rule(
            "jwt",
            re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        ),
        _Rule(
            "api_key",
            re.compile(
                r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|"
                r"github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
                r"AKIA[A-Z0-9]{16})\b"
            ),
        ),
        _Rule(
            "secret",
            re.compile(
                r"(?ix)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
                r"client[_-]?secret|password|passwd|secret)\b\s*[:=]\s*"
                r"(?P<quote>['\"]?)(?P<secret>[^\s,'\"}\]]{6,})(?P=quote)"
            ),
            "secret",
        ),
        _Rule(
            "email",
            re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I),
        ),
        _Rule(
            "user_path",
            re.compile(r"(?i)(?<=\bC:\\Users\\)[^\\\s/:*?\"<>|]+"),
        ),
    )

    @staticmethod
    def _span(rule: _Rule, match: Match[str]) -> Tuple[int, int]:
        return match.span(rule.group) if rule.group else match.span()

    @staticmethod
    def _placeholder(kind: str, index: int) -> str:
        return f"__ATO_{kind.upper()}_{index}__"

    def protect(self, text: str) -> ProtectionSummary:
        if not text:
            return ProtectionSummary(text, {}, {})

        candidates: List[Tuple[int, int, str]] = []
        occupied: List[Tuple[int, int]] = []
        for rule in self._RULES:
            for match in rule.pattern.finditer(text):
                start, end = self._span(rule, match)
                if start == end or any(start < used_end and end > used_start for used_start, used_end in occupied):
                    continue
                candidates.append((start, end, rule.kind))
                occupied.append((start, end))

        if not candidates:
            return ProtectionSummary(text, {}, {})

        replacements: Dict[str, str] = {}
        original_to_placeholder: Dict[Tuple[str, str], str] = {}
        counts: Dict[str, int] = {}
        next_indexes: Dict[str, int] = {}
        protected = text

        for start, end, kind in sorted(candidates, key=lambda item: item[0], reverse=True):
            original = text[start:end]
            identity = (kind, original)
            placeholder = original_to_placeholder.get(identity)
            if placeholder is None:
                index = next_indexes.get(kind, 0) + 1
                placeholder = self._placeholder(kind, index)
                while placeholder in text or placeholder in replacements:
                    index += 1
                    placeholder = self._placeholder(kind, index)
                next_indexes[kind] = index
                counts[kind] = counts.get(kind, 0) + 1
                original_to_placeholder[identity] = placeholder
                replacements[placeholder] = original
            protected = protected[:start] + placeholder + protected[end:]

        return ProtectionSummary(protected, replacements, counts)


_shield: Optional[PrivacyShield] = None


def get_privacy_shield() -> PrivacyShield:
    global _shield
    if _shield is None:
        _shield = PrivacyShield()
    return _shield
