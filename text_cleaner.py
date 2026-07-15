"""
文本清理模块 - 去除Markdown格式

优化版本：
- 预编译正则表达式提升性能
- 合并相关规则减少遍历次数
- 添加更多边界情况处理
"""

import re


# ---- 预编译正则模式（避免重复编译）----
_RE_INLINE_CODE = re.compile(r'`([^`]+)`')
_RE_HEADING = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
_RE_BOLD = re.compile(r'(?<!\*)\*\*(?=\S)(.+?)(?<=\S)\*\*(?!\*)')
_RE_ITALIC = re.compile(r'(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])')
_RE_LINK = re.compile(r'\[([^\]]+)\]\([^)]+\)')
_RE_UNORDERED_LIST = re.compile(r'^[\s]*[-*+]\s+', re.MULTILINE)
_RE_ORDERED_LIST = re.compile(r'^[\s]*\d+\.\s+', re.MULTILINE)
_RE_BLOCKQUOTE = re.compile(r'^[\s]*>\s+', re.MULTILINE)
_RE_HORIZONTAL_RULE = re.compile(r'^[-*_]{3,}$', re.MULTILINE)
_RE_MULTIPLE_BLANK_LINES = re.compile(r'\n{3,}')
_RE_CODE_DECLARATION = re.compile(
    r'^\s*(?:def|class|from|import|async\s+def|function|const|let|var|'
    r'public|private|protected|package|func|fn|#include)\b',
    re.MULTILINE,
)
_RE_ASSIGNMENT = re.compile(r'^\s*[A-Za-z_$][\w.$\[\]]*\s*=\s*\S+', re.MULTILINE)
_RE_CONFIG_LINE = re.compile(r'^\s*[\w.-]+\s*:\s*\S+', re.MULTILINE)
_RE_CODE_OPERATOR = re.compile(r'\b[\w.)\]]+\s+(?:\*|/|%|==|!=|=>)\s+[\w.(\[]+')


def _looks_like_code(text: str) -> bool:
    """Conservatively identify code/config so cleanup cannot rewrite it."""
    if _RE_CODE_DECLARATION.search(text) or _RE_ASSIGNMENT.search(text):
        return True
    if _RE_CODE_OPERATOR.search(text):
        return True
    if len(_RE_CONFIG_LINE.findall(text)) >= 2:
        return True
    if re.search(r'^\s*[-+]\s+\S+', text, re.MULTILINE) and _RE_CONFIG_LINE.search(text):
        return True
    return False


def _clean_prose(text: str) -> str:
    """Remove common Markdown markers from a prose-only segment."""
    text = _RE_INLINE_CODE.sub(r'\1', text)
    text = _RE_HEADING.sub(r'[\1]', text)
    text = _RE_BOLD.sub(r'\1', text)
    text = _RE_ITALIC.sub(r'\1', text)
    text = _RE_LINK.sub(r'\1', text)
    text = _RE_UNORDERED_LIST.sub('  > ', text)
    text = _RE_ORDERED_LIST.sub('  ', text)
    text = _RE_BLOCKQUOTE.sub('  ', text)
    text = _RE_HORIZONTAL_RULE.sub('─' * 40, text)
    return text


def _split_fenced_segments(text: str):
    """Yield (is_code, content) while removing fence marker lines."""
    in_code = False
    buffer = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            if buffer:
                yield in_code, ''.join(buffer)
                buffer = []
            in_code = not in_code
            continue
        buffer.append(line)
    if buffer:
        yield in_code, ''.join(buffer)


def clean_markdown(text: str) -> str:
    """
    清理Markdown格式，转换为纯文本

    Args:
        text: 包含Markdown的文本

    Returns:
        清理后的纯文本
    """
    if not text:
        return text

    segments = []
    for is_code, segment in _split_fenced_segments(text):
        if is_code or _looks_like_code(segment):
            segments.append(segment)
        else:
            segments.append(_clean_prose(segment))
    text = ''.join(segments)

    # 清理多余的空行（最多保留连续2个换行）
    text = _RE_MULTIPLE_BLANK_LINES.sub('\n\n', text)

    # 清理行尾空格
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    text = '\n'.join(lines)

    return text.strip()


def format_for_display(text: str) -> str:
    """
    格式化文本用于显示

    Args:
        text: 原始文本

    Returns:
        格式化后的文本
    """
    # 先清理Markdown
    text = clean_markdown(text)

    # 确保有适当的换行
    text = text.replace('\r\n', '\n')

    return text


# 测试
if __name__ == "__main__":
    test = """### 内容分析

- **内容**：`python main.py`
- **来源**：`python.exe`

```bash
python main.py
```

1. **指定 Python 版本**
   使用 `python3`
"""

    print("Before:")
    print(test)
    print("\n" + "="*50 + "\n")
    print("After:")
    print(clean_markdown(test))
