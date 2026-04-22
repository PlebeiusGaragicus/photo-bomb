# Features

This document describes all implemented features organized by plan step.

## Plan Step 1: Project Setup and Architecture

- **Directory structure**: `src/ui/`, `src/core/`, `src/utils/`
- **Configuration management**: JSON-based config in `~/Library/Preferences/photo-boss/config.json`
- **PyQt6 GUI framework** with modular design

## Plan Step 2: Photos Framework Integration (macOS-specific)

- PyObjC interface to Photos.framework
- Methods for:
  - Listing albums
  - Retrieving photos by album
  - Getting photo metadata (filename, creation date)
- Placeholder authorization flow (actual implementation pending)

## Plan Step 3: Configuration UI and API Connection

**API Settings Dialog** (`src/ui/api_settings_dialog.py`):
- Endpoint URL input
- Model name input
- API key (with masking)
- Health check validation button

**API Client** (`src/core/api_client.py`):
- OpenAI-compatible endpoint support
- Batch analysis method for multiple photos
- HTTP error handling

## Plan Step 4: Main Window Layout and Navigation

**Main Window** (`src/ui/main_window.py`):
- Split-pane layout (30% sidebar, 70% content)
- Menu bar with File → Settings, Exit
- Album sidebar with click-to-select navigation
- Photo grid view with pagination

**Photo Grid** (`src/ui/photo_grid.py`):
- 10×10 grid layout
- Auto-infinite-scroll (triggers on scroll bottom)
- Max 100 photos loaded at once

## Plan Step 5: Photo Analysis Engine

**Analysis Engine** (`src/core/analysis_engine.py`):
- Batch processing orchestration
- Progress signals to UI
- Local caching of results
- Integration with `api_client.Analyze()` method

**Batch Analysis Dialog** (`src/ui/batch_analysis_dialog.py`):
- Progress bar with percentage
- Status updates during analysis
- Results list after completion

## Plan Step 6: Categorization System

**Three Categories**:
| Category | Color | Purpose |
|----------|-------|---------|
| Memories | Green (#4CAF50) | Personal/family photos, important moments |
| Todo | Orange (#FF9800) | Photos with tasks, recipes, diagrams |
| Research | Blue (#2196F3) | Reference materials, documents |

**Features**:
- Category badges in grid view
- Manual categorization toolbar (Memories/Todo/Research buttons)
- Batch categorization support

## Plan Step 7: Album Management

**Album System** (`src/core/album_system.py`):
- Create/delete albums
- Move photos between albums
- Photo counts per album
- System albums: All Photos, Favorites, Recent, Selfies

**Album Sidebar** (`src/ui/album_sidebar.py`):
- Display list of albums with photo counts
- New album input + create button
- Right-click context menu placeholder
