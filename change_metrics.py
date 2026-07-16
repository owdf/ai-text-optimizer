"""Deterministic, local metrics for an AI rewrite."""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re


_WORD_RE = re.compile(r"[A-Za-z0-9_']+|[\u3400-\u9fff]")


@dataclass(frozen=True)
class ChangeMetrics:
    original_chars: int
    result_chars: int
    original_words: int
    result_words: int
    changed_percent: int

    @property
    def character_delta(self) -> int:
        return self.result_chars - self.original_chars

    @property
    def word_delta(self) -> int:
        return self.result_words - self.original_words


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text or ""))


def calculate_change_metrics(original: str, result: str) -> ChangeMetrics:
    original = original or ""
    result = result or ""
    similarity = SequenceMatcher(None, original, result, autojunk=False).ratio()
    changed = round((1.0 - similarity) * 100)
    return ChangeMetrics(
        original_chars=len(original),
        result_chars=len(result),
        original_words=_word_count(original),
        result_words=_word_count(result),
        changed_percent=max(0, min(100, changed)),
    )
