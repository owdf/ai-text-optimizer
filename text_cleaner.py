"""
文本清理模块 - 去除Markdown格式

优化版本：
- 预编译正则表达式提升性能
- 合并相关规则减少遍历次数
- 添加更多边界情况处理
"""

import re


# ---- 预编译正则模式（避免重复编译）----
_RE_CODE_BLOCK_OPEN = re.compile(r'```[\w]*\n?')
_RE_CODE_BLOCK_CLOSE = re.compile(r'```')
_RE_INLINE_CODE = re.compile(r'`([^`]+)`')
_RE_HEADING = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
_RE_BOLD = re.compile(r'\*\*(.+?)\*\*')
_RE_ITALIC = re.compile(r'\*(.+?)\*')
_RE_LINK = re.compile(r'\[([^\]]+)\]\([^)]+\)')
_RE_UNORDERED_LIST = re.compile(r'^[\s]*[-*+]\s+', re.MULTILINE)
_RE_ORDERED_LIST = re.compile(r'^[\s]*\d+\.\s+', re.MULTILINE)
_RE_BLOCKQUOTE = re.compile(r'^[\s]*>\s+', re.MULTILINE)
_RE_HORIZONTAL_RULE = re.compile(r'^[-*_]{3,}$', re.MULTILINE)
_RE_MULTIPLE_BLANK_LINES = re.compile(r'\n{3,}')


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

    # 1. 处理代码块 (```...```) - 保留内容，去掉标记
    text = _RE_CODE_BLOCK_OPEN.sub('', text)
    text = _RE_CODE_BLOCK_CLOSE.sub('', text)

    # 2. 处理行内代码 (`...`) - 去掉反引号保留内容
    text = _RE_INLINE_CODE.sub(r'\1', text)

    # 3. 处理标题 (# ## ### 等) - 转换为 [标题] 格式
    text = _RE_HEADING.sub(r'[\1]', text)

    # 4. 处理加粗 (**...**) - 去掉星号保留内容
    text = _RE_BOLD.sub(r'\1', text)

    # 5. 处理斜体 (*...*) - 去掉星号保留内容（在加粗之后处理，避免冲突）
    text = _RE_ITALIC.sub(r'\1', text)

    # 6. 处理链接 ([text](url)) - 只保留文字部分
    text = _RE_LINK.sub(r'\1', text)

    # 7. 处理列表标记 (- * +) - 用 > 表示列表项
    text = _RE_UNORDERED_LIST.sub('  > ', text)

    # 8. 处理有序列表 (1. 2. 等) - 用空格替换编号
    text = _RE_ORDERED_LIST.sub('  ', text)

    # 9. 处理引用 (>) - 用空格替换
    text = _RE_BLOCKQUOTE.sub('  ', text)

    # 10. 处理水平线 (--- ***) - 用分隔线替代
    text = _RE_HORIZONTAL_RULE.sub('─' * 40, text)

    # 11. 清理多余的空行（最多保留连续2个换行）
    text = _RE_MULTIPLE_BLANK_LINES.sub('\n\n', text)

    # 12. 清理行首行尾空格
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
