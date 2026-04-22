# Photo Boss - README

## Project Setup and Architecture

This directory contains the source code for Photo Boss, a PyQt6 application for macOS that helps users organize their Photos library using vision language models.

### Directory Structure

```
photo-boss/
├── src/                      # Source code
│   ├── __init__.py          # Package init
│   ├── main.py              # Application entry point
│   ├── ui/                  # UI components
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main application window
│   │   ├── photo_grid.py    # Photo grid view with pagination
│   │   ├── category_badge.py # Category tag badges
│   │   ├── album_sidebar.py  # Album sidebar widget
│   │   ├── api_settings_dialog.py # API configuration dialog
│   │   └── batch_analysis_dialog.py # Batch analysis progress dialog
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration management
│   │   ├── photos_library.py # Photos framework integration (PyObjC)
│   │   ├── api_client.py    # OpenAI-compatible API client
│   │   ├── analysis_engine.py # Photo analysis orchestration
│   │   ├── categorization.py # Categorization system
│   │   └── album_system.py  # Album management
│   └── utils/               # Utility functions
│       ├── __init__.py
├── docs/                     # Documentation
│   ├── index.md             # Overview and navigation
│   ├── features.md          # Implemented features
│   ├── architecture.md      # System design
│   ├── api-settings.md      # API configuration guide
│   ├── categorization.md    # Category system details
│   └── photo-access.md      # Photos framework integration
├── assets/                   # Application assets (icons, etc.)
├── pyproject.toml           # Project configuration
└── requirements.txt         # Python dependencies

```

### Dependencies

- PyQt6>=6.5.0 - GUI framework
- requests>=2.31.0 - HTTP client for API calls
- Pillow>=10.0.0 - Image processing
- pyobjc>=10.0 - macOS integration (PyObjC) - only on Darwin

### Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Configuration

Configuration is stored in `~/Library/Preferences/photo-boss/config.json` and includes:
- API endpoint URL (OpenAI-compatible)
- API key
- Model name
- Categories (memories, todo, research)
- Batch size settings

## Features Implemented

1. **Project Setup and Architecture**
   - Python project with proper structure
   - Configuration management system
   - Modular design for UI, core functionality, and utilities

2. **Photos Framework Integration (macOS-specific)**
   - Placeholder interface for PyObjC Photos.framework integration
   - Album listing and photo retrieval methods
   - Authorization handling for library access

3. **Configuration UI and API Connection**
   - Settings dialog for endpoint configuration
   - Health check validation
   - Support for any OpenAI-compatible endpoint

4. **Main Window Layout and Navigation**
   - Split-pane layout with album sidebar + content area
   - Photo grid view with pagination (max 100 photos at a time)
   - Menu bar with settings access

5. **Photo Analysis Engine**
   - Batch processing with progress tracking
   - Integration with vision language models
   - Local caching of analysis results

6. **Categorization System**
   - Three categories: memories, todo, research
   - Color-coded badges for visual identification
   - Manual and batch categorization

7. **Album Management**
   - Album sidebar with photo counts
   - Create/delete album functionality
   - Photo movement between albums

## Next Steps (Deferred)

- Full PyObjC Photos.framework integration
- macOS app bundle packaging
- Error handling and user feedback UI
- Performance optimization for large libraries
- Analytics and usage tracking
