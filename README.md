<div align="center">

# AI Text Optimizer

**A Windows tray assistant that sends selected text to your preferred AI with one global hotkey.**

[![CI](https://github.com/owdf/ai-text-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/owdf/ai-text-optimizer/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/owdf/ai-text-optimizer?display_name=tag)](https://github.com/owdf/ai-text-optimizer/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](#requirements)
[![License](https://img.shields.io/github/license/owdf/ai-text-optimizer)](LICENSE)

[Download for Windows](https://github.com/owdf/ai-text-optimizer/releases/latest) · [中文文档](README_zh.md) · [Report a bug](https://github.com/owdf/ai-text-optimizer/issues/new)

</div>

![Select text, press a hotkey, detect context, ask your AI provider, and copy the result](docs/workflow.svg)

## Why this exists

Fixing a terminal error, translating documentation, or polishing an email often means leaving the current app, opening a chat window, pasting text, waiting, and copying the result back.

AI Text Optimizer keeps that workflow inside the app you are already using:

1. Select text in any Windows application.
2. Press `Ctrl+Shift+Q` (customizable).
3. Review the AI result and copy it with one click.

The app detects the foreground application, estimates whether the selection is code, an error, a log, configuration, or plain text, and chooses an appropriate prompt template. You remain in control of the template and AI provider.

## What makes it different

Most rewriting tools are browser editors built around tone presets. AI Text Optimizer is a local-first technical workflow layer:

- **Privacy Shield before the request:** high-confidence credentials, authorization tokens, email addresses, and Windows usernames are replaced locally before text reaches the configured provider. Surviving placeholders are restored only in the local result.
- **Technical context, not generic paraphrasing:** the app routes code, stack traces, logs, and configuration to purpose-built prompts using the foreground application as context.
- **Refine without starting over:** turn the visible result into a shorter version, a clearer version, or a prioritized action plan without copying it into another chat.
- **Inspectable change metrics:** every result shows a deterministic local change percentage and character delta. No second AI call is used for this calculation.
- **Bring your own model:** use a compatible cloud API or a loopback model such as Ollama; the project does not require an account or proxy requests through its own server.

## Features

- Global, customizable Windows hotkey.
- Context-aware prompt routing for code, errors, logs, configuration, translation, and summaries.
- Ten built-in templates plus editable custom templates.
- OpenAI-compatible APIs, Anthropic-compatible requests, and local Ollama support.
- Chinese and English interface.
- Default-on local Privacy Shield with a visible protected-item count.
- One-click **Shorter**, **Clearer**, and **Action plan** follow-up refinements.
- Local before/after change metrics.
- Clipboard restoration: the clipboard content that existed before selection capture is restored.
- Tray-based settings for provider, endpoint, model, API key, hotkey, and language.
- HTTPS enforcement for remote custom endpoints; HTTP is accepted only for loopback services.

## Install the Windows release

### Requirements

- Windows 10 or Windows 11.
- An API key for a supported cloud provider, or a local OpenAI-compatible service such as Ollama.

### Steps

1. Open [the latest release](https://github.com/owdf/ai-text-optimizer/releases/latest).
2. Download `AITextOptimizer-Windows-x64.zip`.
3. Optionally verify the archive against `SHA256SUMS.txt`.
4. Extract the archive and run `AITextOptimizer.exe`.
5. Right-click the tray icon, open **Settings**, and configure your provider.

The executable is not code-signed yet, so Windows SmartScreen may show an “unknown publisher” warning. Verify that the file came from this repository and check its SHA-256 checksum before running it.

Packaged builds store configuration, custom templates, and logs under `%LOCALAPPDATA%\AITextOptimizer`. If a `config.json` already exists beside the executable, it is used as a portable configuration instead.

## Run from source

```powershell
git clone https://github.com/owdf/ai-text-optimizer.git
cd ai-text-optimizer
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.example.json config.json
python main.py
```

Python 3.10 or newer is supported. The application itself targets Windows because selection capture, active-window detection, and global input handling use Windows APIs.

## Provider configuration

Use the tray **Settings** window whenever possible. The equivalent JSON structure is:

```json
{
  "ai_service": {
    "provider": "openai",
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o",
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "hotkey": {
    "trigger": "ctrl+shift+q",
    "enabled": true
  },
  "privacy": {
    "enabled": true
  }
}
```

The `openai` provider works with services implementing `/v1/chat/completions`. Choose `anthropic` for the Anthropic Messages API. Loopback endpoints such as `http://localhost:11434/v1` can be used without an API key.

## Privacy and security

- Only text captured after the configured hotkey is pressed is sent for processing.
- If selection capture does not produce new clipboard content, the previous clipboard value is not submitted.
- Privacy Shield is enabled by default. It detects high-confidence secrets and identifiers locally, replaces them with typed placeholders for each outbound request, and restores exact placeholders in the local response.
- Privacy Shield is a safety layer, not a complete data-loss-prevention system. Review unusually sensitive selections and use a local model when text must never leave the device.
- Selected text is sent to the provider configured by the user; review that provider's data policy before sending confidential material.
- API keys are stored in the local application configuration and are never committed by the project.
- Remote custom endpoints must use HTTPS. Plain HTTP is limited to loopback hosts for local models.

## Development

Run the complete test suite:

```powershell
python -m pip install pytest -r requirements.txt
python -m pytest -q
```

Build the standalone executable:

```powershell
python -m pip install pyinstaller
python build.py
```

The output is `dist/AITextOptimizer.exe`. CI runs the tests on Python 3.10 and 3.12 and performs a real Windows packaging smoke test. Pushing a `v*` tag builds the release archive and publishes its checksum.

## Project structure

```text
main.py                 Application lifecycle and UI coordination
ai_service.py           OpenAI-compatible and Anthropic API adapters
context_analyzer.py     Foreground-window and text classification heuristics
privacy_shield.py       Local credential and identifier redaction
change_metrics.py       Deterministic before/after metrics
clipboard.py            Selection capture and clipboard restoration
hotkey.py               Global hotkey listener
prompt_templates.py     Built-in and custom prompt templates
config.py               Persistent settings
ui/                     Tray, result, settings, hotkey, and template windows
tests/                  Regression and unit tests
build.py                PyInstaller build entry point
```

## Known limitations

- Windows only.
- Responses are currently displayed after the provider finishes; token streaming is not yet implemented.
- A processing request must finish before another hotkey request can start.
- Context classification is heuristic and can be overridden by selecting a template manually.

## Contributing

Issues and pull requests are welcome. For a bug report, include the Windows version, Python or release version, provider type, steps to reproduce, and relevant logs with secrets removed.

## License

[MIT](LICENSE) © 2026 Dongfang Wang.
