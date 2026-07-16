from change_metrics import calculate_change_metrics


def test_identical_text_has_zero_change():
    metrics = calculate_change_metrics("hello world", "hello world")
    assert metrics.changed_percent == 0
    assert metrics.character_delta == 0
    assert metrics.word_delta == 0


def test_reports_shorter_rewrite():
    metrics = calculate_change_metrics("This is a very long sentence.", "A short sentence.")
    assert metrics.changed_percent > 0
    assert metrics.character_delta < 0
    assert metrics.word_delta < 0


def test_handles_chinese_without_spaces():
    metrics = calculate_change_metrics("这是原始文本", "这是优化文本")
    assert metrics.original_words == 6
    assert metrics.result_words == 6
    assert metrics.changed_percent > 0
