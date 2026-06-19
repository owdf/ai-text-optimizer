[中文文档](README_zh.md)

# AI Text Optimizer

A lightweight Windows desktop tool that sends selected text to AI for analysis and optimization. Supports multiple AI services, smart prompt templates, and bilingual interface.

## Features

- Global hotkey trigger
- Clipboard monitor mode
- Auto-detect source application
- Smart prompt templates
- Multiple AI service support
- Custom hotkey (press to set)
- System tray background run

## Installation

### Requirements

- Windows 10/11
- Python 3.8+

### Install dependencies

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| customtkinter | GUI framework |
| pynput | Global hotkey |
| pystray | System tray |
| requests | HTTP requests |
| pyperclip | Clipboard |
| Pillow | Image processing |

## Usage

### Start

```bash
python main.py
```

### Steps

1. Select text in any application
2. Press Ctrl+C to copy
3. Press hotkey (default: Ctrl+Shift+Q)
4. View AI analysis result

### Tray menu

Right-click the tray icon in system tray:

- Hotkey display - Click to open hotkey settings
- Hotkey ON/OFF
- Templates - Open template manager
- Settings - Open settings
- Language - Switch Chinese/English
- Quit

## Hotkey Settings

Supports "press to set" mode:

1. Click "Start Listening"
2. Press desired hotkey combination
3. Auto-saved

Press ESC to cancel.

Preset buttons available:
- Ctrl+Q
- Ctrl+Shift+Q
- Alt+Q

## Prompt Templates

### Built-in templates

| Template | Category | Description |
|----------|----------|-------------|
| [Bug] Code Fix | Code | Analyze error and provide fix |
| [Code] Optimize | Code | Optimize performance |
| [Code] Explain | Code | Explain code functionality |
| [Code] Review | Code | Code review with suggestions |
| [Bug] Debug | Debug | Debug and trace issues |
| [Bug] Stack Trace | Debug | Analyze stack traces |
| [Config] Fix | Config | Fix configuration issues |
| [Log] Analyze | Log | Analyze logs |
| [General] Translate | General | Translate text |
| [General] Summarize | General | Summarize content |

### Custom templates

1. Open template manager
2. Click "Add"
3. Fill in fields:
   - Key: unique identifier
   - Name: display name
   - Description
   - Category
   - Prompt content
4. Save

Available variables in prompt:
- `{text}` - Selected text
- `{source}` - Source application
- `{language}` - Programming language

## AI Service Configuration

### Supported services

| Service | Base URL | Models |
|---------|----------|--------|
| OpenAI | https://api.openai.com/v1 | gpt-4, gpt-3.5-turbo |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Zhipu AI | https://open.bigmodel.cn/api/paas/v4 | glm-4 |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |
| Qwen | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |
| Ollama (local) | http://localhost:11434/v1 | llama3 |
| Claude | https://api.anthropic.com/v1 | claude-3-sonnet |

### Setup steps

1. Right-click tray icon -> Settings
2. Select preset service or enter custom
3. Enter API Key
4. Click "Test Connection"
5. Save

## Configuration File

`config.json` - Main configuration file

```json
{
  "ai_service": {
    "provider": "openai_compatible",
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  },
  "hotkey": {
    "trigger": "ctrl+shift+q",
    "enabled": true
  },
  "clipboard": {
    "wait_mode_timeout": 15,
    "check_interval": 0.2
  },
  "general": {
    "language": "auto",
    "enable_logging": false
  }
}
```

## Project Structure

```
ai-text-optimizer/
|-- main.py                  # Entry point
|-- config.py                # Configuration manager
|-- config.json              # Configuration file (gitignored)
|-- config.example.json      # Example configuration
|-- ai_service.py            # AI service adapter
|-- prompt_templates.py      # Prompt template manager
|-- context_analyzer.py      # Context analyzer
|-- clipboard.py             # Clipboard operations
|-- hotkey.py                # Hotkey listener
|-- text_cleaner.py          # Markdown cleaner
|-- language.py              # Multi-language support
|-- icons.py                 # Icon generator
|-- requirements.txt         # Dependencies
|-- README.md                # Documentation (English)
|-- README_zh.md             # Documentation (Chinese)
|-- ui/
|   |-- __init__.py
|   |-- floating_window.py   # Result window
|   |-- settings_window.py   # Settings window
|   |-- hotkey_window.py     # Hotkey settings
|   |-- template_window.py   # Template manager
|   |-- tray.py              # System tray
```

## FAQ

### Q: Hotkey not working?

A: Check if another application is using the same hotkey. Try setting a new hotkey via tray menu.

### Q: AI returns Markdown format?

A: The program automatically cleans Markdown. If it still appears, check if text_cleaner.py is working.

### Q: How to change language?

A: Right-click tray icon -> Language -> Select Chinese or English.

### Q: How to add custom prompt template?

A: Right-click tray icon -> Templates -> Click "Add" -> Fill in and save.

### Q: Which AI services are supported?

A: Any service compatible with OpenAI API format. See the service table above.

## License

MIT License
