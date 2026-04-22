# Categorization

## Categories

| Name | Hex | Intended for |
|------|-----|--------------|
| `memories` | `#4CAF50` | Personal/family photos, events |
| `todo` | `#FF9800` | Captured tasks, recipes, lists, diagrams |
| `research` | `#2196F3` | Reference material, documents, articles |

The set is also embedded in the system + user prompts inside
`core/api_client.py::analyze_photo` and in `Config.defaults["categories"]`.
**Adding a category requires changes in all four locations** (see "Single
source of truth" below).

## Where the data lives

| Concern | File | Notes |
|---------|------|-------|
| Canonical category list | `core/categorization.py::CategorizationSystem.categories` | Class is **never instantiated**; this list is currently dead |
| Color map (core copy) | `core/categorization.py::CategorizationSystem._category_colors` | Dead |
| Color map (UI copy) | `ui/category_badge.py::CategoryBadge.COLORS` | The one actually rendered |
| Default config copy | `core/config.py::Config.defaults["categories"]` | Read but never written |
| Prompt copy | `core/api_client.py::analyze_photo` system + user content | Hardcoded strings |

This is duplication, not design. Consolidating onto `CategorizationSystem`
as the single source of truth - and deleting the others - is one of the
top cleanup tasks.

## How the UI categorizes today

`MainWindow._on_categorize_clicked`:

1. Reads `self.sender()` to map button -> category string.
2. Constructs `CategoryBadge(category)` and **immediately drops it on the
   floor** (no parent, no insertion into any layout).
3. Writes `f"Photo categorized as: {category}"` to the status bar.

There is no persistence. Re-selecting the same photo loses the assignment.

## How analysis would categorize (when wired)

`api_client.analyze_photo` instructs the model to return:

```json
{
  "category": "memories|todo|research",
  "confidence": 0.0,
  "tags": ["..."],
  "description": "..."
}
```

`PhotoAnalysisEngine` (currently dead code) is the intended consumer; it
caches results in an in-process dict and emits `photo_analyzed(photo_id,
result)`. No on-disk cache yet despite `_save_cache` / `_load_cache`
placeholder methods.

## Visual badge

`ui/category_badge.py::CategoryBadge` is a `QFrame` with a colored `QLabel`
and a non-functional dropdown caret button. `category_changed(str)` signal
is declared but nothing connects to it.
