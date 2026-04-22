# Categorization System

Photo Boss uses three fixed categories to organize photos.

## Categories

### Memories 🟢 Green

**Purpose**: Personal/family photos, important moments, events

**Examples**:
- Family gatherings, weddings, birthdays
- Vacation and travel photos
- Portrait photos of loved ones
- Milestone events (graduations, anniversaries)
- Sentimental snapshots

**Visual**: `memories` badge appears green in grid view

---

### Todo 🟠 Orange

**Purpose**: Photos containing tasks, instructions, or things to remember/do

**Examples**:
- Recipe pages or cooking instructions
- To-do lists written on paper
- Diagrams or whiteboard notes
- Product manuals or assembly guides
- Installation instructions
- Work tasks captured as photos

**Visual**: `todo` badge appears orange in grid view

---

### Research 🔵 Blue

**Purpose**: Reference materials, documents, articles for study or information

**Examples**:
- Articles or blog posts saved as images
- Documentation pages
- Study notes or textbooks
- Scientific papers
- How-to guides and tutorials
- Historical documents

**Visual**: `research` badge appears blue in grid view

---

## Usage

### Manual Categorization

1. Select a photo (click in grid)
2. Click one of the category buttons:
   - **Memories**
   - **Todo**
   - **Research**
3. Badge updates on that photo
4. Status bar confirms: `"Photo categorized as: memories"`

### Batch Categorization

Use the **Analyze Selected Photos** button:
1. Select photos to analyze (or leave unselected for visible batch)
2. Click **Analyze Selected Photos**
3. Vision model analyzes each photo and suggests category
4. Review results in batch dialog
5. Apply categories as needed

## Categorization API Response Format

When analyzing with vision model, expect JSON:
```json
[
  {
    "photo_id": "ABC-123-DEF",
    "category": "memories",
    "confidence": 0.92,
    "reasoning": "Family gathering photo showing multiple people smiling"
  }
]
```

## Category Badge Implementation

**File**: `src/ui/category_badge.py`

Badges display:
- Category name (short: memories/todo/research)
- Color-coded background
- Click-through to view category details (future enhancement)
