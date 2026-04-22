# Photo Boss Documentation

A PyQt6 macOS application for organizing Photos library using vision language models.

## Quick Start

```bash
cd photo-boss
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Navigation

| Document | Description |
|----------|-------------|
| [Features](./features.md) | Implemented features (7 plan steps) |
| [Architecture](./architecture.md) | System design and module responsibilities |
| [API Settings](./api-settings.md) | Configure OpenAI-compatible vision models |
| [Categorization](./categorization.md) | Memories, Todo, Research system |
| [Photo Access](./photo-access.md) | macOS Photos framework integration |

## What is Photo Boss?

Photo Boss helps macOS users organize their Photos library by:
- Analyzing photos with vision language models (VLMs)
- Categorizing into **memories**, **todo**, or **research**
- Managing albums and moving photos between them
- Manual batch processing (user-triggered, no automatic scanning)

**Key constraints:**
- macOS only (uses Photos framework via PyObjC)
- No hardcoded endpoints — users bring their own VLM
- Max 100 photos loaded at once for performance
- Fully offline, no analytics

## Development Status

✓ All 7 plan steps completed:
1. Project setup and architecture
2. Photos Framework Integration (macOS-specific)
3. Configuration UI and API Connection
4. Main Window Layout and Navigation
5. Photo Analysis Engine
6. Categorization System
7. Album Management

See [Features](./features.md) for details.
