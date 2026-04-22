# Architecture

High-level system design and module responsibilities.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Main Window  │  │  Photo Grid  │  │Batch Dialog  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                     Core Logic Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Config Manager│  │Analysis Engine│ │Album System  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │API Client    │  │Categorization│                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                 Platform Integration Layer                  │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │Photos Wrapper│  │ Local Cache   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### UI Layer (`src/ui/`)

| File | Responsibility |
|------|----------------|
| `main_window.py` | Main window, menu bar, album sidebar, toolbar |
| `photo_grid.py` | Grid view with pagination (max 100 photos) |
| `category_badge.py` | Visual category tags |
| `api_settings_dialog.py` | Endpoint configuration dialog |
| `batch_analysis_dialog.py` | Progress display during batch analysis |
| `album_sidebar.py` | Album list management widget |

### Core Layer (`src/core/`)

| File | Responsibility |
|------|----------------|
| `config.py` | JSON config loading/saving, API settings storage |
| `photos_library.py` | PyObjC wrapper for Photos.framework |
| `api_client.py` | OpenAI-compatible HTTP client |
| `analysis_engine.py` | Batch processing orchestration with progress signals |
| `categorization.py` | Three-category system (memories/todo/research) |
| `album_system.py` | Album CRUD operations, photo management |

### Utils Layer (`src/utils/`)

| File | Responsibility |
|------|----------------|
| `helpers.py` | Configuration directory paths, utilities |

## Data Flow

### Photo Analysis Flow
```
User clicks "Analyze" → BatchAnalysisDialog opens
  ↓
analysis_engine.process_batch() starts in background thread
  ↓
For each photo:
  - Load photo data from Photos library (cached)
  - Send to API client (analyze_photo())
  - Parse vision model response
  - Store result with caching
  ↓
Progress signals emitted → UI updates progress bar
  ↓
Complete signal → Results displayed in dialog
```

### Photo Display Flow
```
Album selection changes
  ↓
_main_window._load_photo_batch()
  ↓
photos_library.get_photos_for_album(album_id, offset, limit)
  ↓
photo_grid.clear() + add_photo_item() for each photo
```

## Configuration Storage

**Location**: `~/Library/Preferences/photo-boss/config.json`

**Schema**:
```json
{
  "api_endpoint": "https://api.openai.com/v1/chat/completions",
  "model_name": "gpt-4o-mini",
  "api_key": "...",
  "categories": ["memories", "todo", "research"],
  "batch_size": 50
}
```

## Signal Flow (Qt)

- `photo_grid.batch_requested(offset, limit)` → `_load_photo_batch()`
- `photo_grid.photo_selected(photo_id)` → `_on_photo_selected()`
- `analysis_engine.progress(percent)` → progress bar update
- `analysis_engine.complete(results)` → results list population
