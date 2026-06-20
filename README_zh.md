[English](README.md)

# AI Text Optimizer

**选中文字 → 按一下快捷键 → AI帮你改好，直接粘贴回去**

写邮件、改代码、润色文案，不用切换窗口，不用打开网页。

---

## 一句话说清

**不用打开任何网页/APP，选中文字按一下就完事。**

跟浏览器插件、ChatGPT网页版的核心区别：**系统级快捷键 + 托盘后台运行 + 多AI支持**。

## 效果演示

<!-- 录一个15秒GIF放这里：选中文字 → 按Ctrl+Shift+Q → 结果弹出 -->
<!-- 推荐用 ScreenToGif 录制，文件放项目根目录 -->

```
┌─────────────────────────────────────────────────────────┐
│  任意应用中选中文字                                        │
│         ↓                                               │
│  按 Ctrl+Shift+Q                                        │
│         ↓                                               │
│  AI结果窗口弹出，直接粘贴回去                               │
└─────────────────────────────────────────────────────────┘
```

> 实际效果比这好看10倍 —— 录个GIF替换这段

## 为什么用这个？

| 场景 | 痛点 | 这个工具怎么解决 |
|------|------|-----------------|
| 写英文邮件 | 不确定语法对不对 | 选中 → 一键润色 → 粘贴回去 |
| 代码报错 | 复制粘贴到ChatGPT太麻烦 | 选中报错 → 按快捷键 → 直接看修复方案 |
| 看英文文档 | 要切窗口翻译 | 选中 → 按快捷键 → 翻译结果就地弹出 |
| 写文案 | 反复改措辞 | 选中 → 按快捷键 → AI帮你改好 |

## 核心功能

- **系统级快捷键** — 任意应用中都能用，不用切窗口
- **托盘后台运行** — 不占任务栏，安静待命
- **多AI支持** — OpenAI、DeepSeek、Claude、通义千问、本地Ollama...
- **智能模板** — 内置代码修复、翻译、总结等10+场景模板
- **中英双语** — 界面支持中文/English切换

## 3分钟上手

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/ai-text-optimizer.git
cd ai-text-optimizer

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置AI服务

```bash
# 复制示例配置
cp config.example.json config.json

# 编辑 config.json，填入你的API Key
```

或者启动后右键托盘图标 → **设置** → 选择AI服务 → 填入API Key → 测试连接 → 保存

### 3. 启动

```bash
python main.py
```

右下角出现托盘图标，开始使用！

### 4. 使用

1. **选中任意文字**
2. **按 `Ctrl+Shift+Q`**（可自定义）
3. **AI结果窗口弹出，直接粘贴回去**

## 自定义热键

支持"按下即设"模式：

1. 右键托盘图标 → 热键显示
2. 点击"开始监听"
3. 按下想要的热键组合（如 `Ctrl+Q`、`Alt+Q`）
4. 自动保存

按ESC取消。

## 支持的AI服务

| 服务 | 说明 |
|------|------|
| OpenAI | GPT系列 |
| DeepSeek | DeepSeek系列 |
| 智谱AI | GLM系列 |
| 月之暗面 | Kimi系列 |
| 通义千问 | Qwen系列 |
| Claude | Claude系列 |
| Ollama | 本地部署，免费使用 |

> 任何兼容OpenAI API格式的服务都能用，支持最新模型

> 任何兼容OpenAI API格式的服务都能用

## 自定义模板

右键托盘图标 → 提示词模板 → 添加

可用变量：
- `{text}` — 选中的文本
- `{source}` — 来源应用
- `{language}` — 编程语言

## 项目结构

```
ai-text-optimizer/
├── main.py                  # 主程序入口
├── config.py                # 配置管理
├── ai_service.py            # AI服务适配层
├── prompt_templates.py      # 提示词模板管理
├── context_analyzer.py      # 上下文分析器
├── clipboard.py             # 剪贴板操作
├── hotkey.py                # 热键监听
├── text_cleaner.py          # Markdown清理
├── language.py              # 多语言支持
└── ui/
    ├── floating_window.py   # 结果窗口
    ├── settings_window.py   # 设置窗口
    ├── hotkey_window.py     # 热键设置
    ├── template_window.py   # 模板管理
    └── tray.py              # 系统托盘
```

## 常见问题

**Q: 热键不工作？**
检查是否有其他应用占用了相同热键。尝试通过托盘菜单设置新热键。

**Q: AI返回Markdown格式？**
程序会自动清理Markdown格式。如果仍然出现，检查 `text_cleaner.py` 是否正常工作。

**Q: 支持哪些AI服务？**
任何兼容OpenAI API格式的服务都支持。

## 许可证

MIT License

---

如果觉得有用，点个 star 支持一下！
