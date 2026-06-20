[中文文档](README_zh.md)

# AI Text Optimizer

**Select text → Press a hotkey → AI fixes it → Paste back**

Write emails, fix code, polish copy — no window switching, no browser tabs.

---

## What it does

**No web app, no browser extension. Select text, press one key, done.**

The difference from browser plugins and ChatGPT: **system-wide hotkey + tray background + multi-AI support**.

## Demo

<!-- Record a 15-second GIF: select text → press Ctrl+Shift+Q → result pops up -->
<!-- Use ScreenToGif, put the file in project root -->

```
┌─────────────────────────────────────────────────────────┐
│  Select text in any app                                  │
│         ↓                                               │
│  Press Ctrl+Shift+Q                                     │
│         ↓                                               │
│  AI result window pops up, paste it back                 │
└─────────────────────────────────────────────────────────┘
```

> The real thing looks 10x better — replace this with a GIF

## Why use this?

| Scenario | Pain point | How this helps |
|----------|------------|----------------|
| Writing emails in English | Not sure about grammar | Select → One-click polish → Paste back |
| Code errors | Copy-pasting to ChatGPT is tedious | Select error → Hotkey → See fix directly |
| Reading English docs | Switching windows to translate | Select → Hotkey → Translation appears in place |
| Writing copy | Endless rewording | Select → Hotkey → AI rewrites it |

## Key features

- **System-wide hotkey** — Works in any app, no window switching
- **Tray background** — Stays out of taskbar, quietly waiting
- **Multi-AI support** — OpenAI, DeepSeek, Claude, Qwen, local Ollama...
- **Smart templates** — 10+ built-in templates for code fix, translation, summary, etc.
- **Bilingual UI** — Chinese / English interface

## Get started in 3 minutes

### 1. Install

```bash
# Clone
git clone https://github.com/yourusername/ai-text-optimizer.git
cd ai-text-optimizer

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AI service

```bash
# Copy example config
cp config.example.json config.json

# Edit config.json, add your API key
```

Or after launch: right-click tray icon → **Settings** → Select AI service → Enter API key → Test connection → Save

### 3. Launch

```bash
python main.py
```

Tray icon appears in bottom-right corner. You're ready!

### 4. Use

1. **Select any text**
2. **Press `Ctrl+Shift+Q`** (customizable)
3. **AI result window pops up, paste it back**

## Custom hotkey

Supports "press to set" mode:

1. Right-click tray icon → Hotkey display
2. Click "Start listening"
3. Press your desired key combo (e.g. `Ctrl+Q`, `Alt+Q`)
4. Auto-saved

Press ESC to cancel.

## Supported AI services

| Service | Details |
|---------|---------|
| OpenAI | GPT series |
| DeepSeek | DeepSeek series |
| Zhipu AI | GLM series |
| Moonshot | Kimi series |
| Qwen | Qwen series |
| Claude | Claude series |
| Ollama | Local deployment, free to use |

> Any service compatible with OpenAI API format works, supports latest models

> Any service compatible with OpenAI API format works

## Custom templates

Right-click tray icon → Prompt templates → Add

Available variables:
- `{text}` — Selected text
- `{source}` — Source application
- `{language}` — Programming language

## Project structure

```
ai-text-optimizer/
├── main.py                  # Entry point
├── config.py                # Configuration manager
├── ai_service.py            # AI service adapter
├── prompt_templates.py      # Prompt template manager
├── context_analyzer.py      # Context analyzer
├── clipboard.py             # Clipboard operations
├── hotkey.py                # Hotkey listener
├── text_cleaner.py          # Markdown cleaner
├── language.py              # Multi-language support
└── ui/
    ├── floating_window.py   # Result window
    ├── settings_window.py   # Settings window
    ├── hotkey_window.py     # Hotkey settings
    ├── template_window.py   # Template manager
    └── tray.py              # System tray
```

## FAQ

**Q: Hotkey not working?**
Check if another app is using the same hotkey. Try setting a new one via tray menu.

**Q: AI returns Markdown format?**
The program auto-cleans Markdown. If it still appears, check if `text_cleaner.py` is working.

**Q: Which AI services are supported?**
Any service compatible with OpenAI API format.

## License

MIT License

---

If you find this useful, give it a star!
