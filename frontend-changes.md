# Frontend Changes Documentation

This document tracks all frontend changes across the RAG Chatbot project.

---

## Dark Mode Toggle Implementation (ui_feature branch)

### Summary
Added a dark mode toggle button to the frontend that allows users to switch between dark and light themes. The toggle preserves user preference using localStorage and includes full accessibility support.

### Files Modified

#### 1. `index.html`
**Changes:**
- Added theme toggle button in the header section
- Button positioned in top-right corner
- Includes SVG icons for sun (light mode) and moon (dark mode)
- Added accessibility attributes:
  - `aria-label="Toggle dark mode"`
  - `title="Toggle theme"`
  - `id="themeToggle"`
  - `class="theme-toggle"`
- Updated version reference from `v=12` to `v=13`

#### 2. `style.css`
**Changes:**
- Added **Light Mode CSS Variables** under `:root.light-mode`
- Added header styling to make it visible (was `display: none`)
- Added theme toggle button styles with animations
- Added smooth transitions for all color changes
- Updated link styling to work in both themes
- Updated code/pre styling for better light mode contrast

#### 3. `script.js`
**Changes:**
- Added theme state management (`isDarkMode` variable)
- Added `toggleTheme()` function
- Added `loadThemePreference()` function
- Added keyboard accessibility for theme toggle (Space/Enter)
- Added localStorage persistence for theme preference
- Updated `aria-label` dynamically based on current theme

### Features Implemented
- ✅ Dark Mode Toggle Button (circular, top-right)
- ✅ Smooth Transitions (0.3s, custom easing)
- ✅ State Management (localStorage persistence)
- ✅ Accessibility (ARIA labels, keyboard support, focus styles)
- ✅ Visual Design (two themes: dark and light)

---

## Code Quality Tools Implementation (main branch)

### Summary
Added comprehensive code quality tools to the RAG Chatbot development workflow to ensure consistent, maintainable, and high-quality code.

### Changes Made

#### 1. Updated `pyproject.toml`
Added development dependencies and tool configurations:
- `black==24.10.0` - Code formatter
- `flake8==7.1.1` - Linter
- `pytest==8.3.4` - Test runner

#### 2. Created Development Scripts
- `format.sh` - Automated Black formatter
- `check-quality.sh` - Comprehensive quality verification (format + lint + test)

#### 3. Created `DEVELOPMENT.md`
Complete development guide covering tool setup, usage, guidelines, and CI/CD integration.

#### 4. Formatted Codebase
Applied Black formatting to 35+ Python files with 100-character line limit.

### Files Modified
**Core Backend:** `ai_generator.py`, `app.py`, `config.py`, `document_processor.py`, `models.py`, `rag_system.py`, `search_tools.py`, `session_manager.py`, `vector_store.py`

**Test Suite:** `conftest.py` (NEW), `test_api_endpoints.py` (NEW), all existing tests formatted

**Root Files:** `main.py`, `test_migration.py`, `uv.lock`, `pyproject.toml`

**Documentation:** `DEVELOPMENT.md` (NEW), `frontend-changes.md` (NEW)

**Scripts:** `format.sh` (NEW), `check-quality.sh` (NEW)

### Usage
```bash
# Format code
./format.sh

# Run quality checks
./check-quality.sh

# Install dev tools
uv pip install -e .[dev]
```

---

## Implementation Dates
- **Dark Mode Toggle**: December 28, 2025 (ui_feature branch)
- **Code Quality Tools**: December 28, 2025 (main branch)

## Impact
- **Dark Mode**: User experience enhancement with theme switching
- **Code Quality**: Development workflow improvement with automated tools

Both features are backward compatible and non-breaking.
