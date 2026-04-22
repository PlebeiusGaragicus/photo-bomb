# Photo Boss Documentation

## Quick Start

```bash
cd photo-boss
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Overview

Photo Boss is a PyQt6 macOS application that helps users organize their Photos library using vision language models (VLMs).

### Features

- 📸 Analyze photos with OpenAI-compatible VLM endpoints
- 🏷️ Categorize into **memories**, **todo**, or **research**
- 🗂️ Manage albums and move photos between them
- ⚡ Manual batch processing (user-triggered, no auto-scan)

### Constraints

- macOS only (uses Photos framework via PyObjC)
- No hardcoded endpoints — users bring their own VLM
- Max 100 photos loaded at once for performance
- Fully offline, no analytics tracking

## Documentation Structure

| Document | Description |
|----------|-------------|
| [Index](docs/index.md) | Overview and quick start guide |
| [Features](docs/features.md) | Implemented features (7 plan steps) |
| [Architecture](docs/architecture.md) | System design and module responsibilities |
| [API Settings](docs/api-settings.md) | Configure vision models |
| [Categorization](docs/categorization.md) | Memories, Todo, Research system |
| [Photo Access](docs/photo-access.md) | macOS Photos framework integration |

## Development Plan

✅ **Completed (7/7)**:
1. Project Setup and Architecture
2. Photos Framework Integration (macOS-specific)
3. Configuration UI and API Connection
4. Main Window Layout and Navigation
5. Photo Analysis Engine
6. Categorization System
7. Album Management

See [Features](docs/features.md) for implementation details.

## Getting Help

- Check the documentation links above
- Review example configuration in `config.py`
- See `src/ui/` for UI component examples
