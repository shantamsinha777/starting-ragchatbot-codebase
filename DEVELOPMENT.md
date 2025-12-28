# Development Guide

This guide covers the development workflow for the RAG Chatbot codebase, including code quality tools and best practices.

## Quick Start

```bash
# Install development dependencies
uv pip install -e .[dev]

# Run quality checks
./check-quality.sh

# Format code
./format.sh
```

## Code Quality Tools

### 1. Black Formatter
- **Line length**: 100 characters
- **Target version**: Python 3.13
- **Configuration**: `pyproject.toml`

**Usage:**
```bash
# Format all files
./format.sh

# Check formatting
uv run black --check backend/ main.py test_migration.py --line-length 100 --target-version py313
```

### 2. Flake8 Linting
- **Max line length**: 100 characters
- **Ignored rules**: E203, W503 (whitespace before/after colon, line break before binary operator)

**Usage:**
```bash
# Run linting
uv run flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503
```

### 3. Pytest Testing
- **Test discovery**: `backend/tests/`
- **Test patterns**: `test_*.py`, `*_test.py`
- **Markers**: unit, integration, api, mock, real_api, slow

**Usage:**
```bash
# Run all tests
uv run pytest backend/tests/

# Run with coverage
uv run pytest --cov=backend backend/tests/

# Run specific test types
uv run pytest -m "unit"
uv run pytest -m "integration"
```

## Development Scripts

### `format.sh`
Automatically formats all Python files in the project:
- `backend/` directory
- `main.py`
- `test_migration.py`

### `check-quality.sh`
Runs comprehensive quality checks:
1. **Black format check** - Ensures consistent formatting
2. **Flake8 linting** - Code quality and style
3. **Pytest tests** - Unit and integration tests

## Code Style Guidelines

### Imports
- Use absolute imports where possible
- Group imports: standard library, third-party, local modules
- Remove unused imports (flake8 will catch these)

### Line Length
- Maximum 100 characters per line
- Break long lines appropriately using parentheses

### Docstrings
- Use triple quotes for docstrings
- Follow Google or NumPy style
- Include parameter types and return values

### Type Hints
- Use type hints for function signatures
- Import types from `typing` module as needed

## Project Structure

```
/home/shantam/starting-ragchatbot-codebase/
├── backend/
│   ├── ai_generator.py      # AI integration with OpenRouter
│   ├── rag_system.py        # Main orchestrator
│   ├── vector_store.py      # ChromaDB storage
│   ├── document_processor.py # Text processing
│   ├── search_tools.py      # Tool definitions
│   ├── session_manager.py   # Conversation history
│   ├── config.py            # Configuration
│   ├── models.py            # Data models
│   ├── app.py               # FastAPI server
│   └── tests/               # Comprehensive test suite
├── frontend/                # Static web interface
├── docs/                    # Course documents
├── main.py                  # Entry point
├── test_migration.py        # Migration testing
├── format.sh               # Code formatter
├── check-quality.sh        # Quality checker
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lock file
```

## Environment Setup

### Prerequisites
- Python 3.13+
- uv package manager
- OpenRouter API key (in `.env` file)

### Installation
```bash
# Install all dependencies including dev tools
uv pip install -e .[dev]

# Verify installation
uv run black --version
uv run flake8 --version
uv run pytest --version
```

### Environment Variables
Create a `.env` file with:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=xiaomi/mimo-v2-flash:free
```

## Debugging

### Enable Debug Output
The `ai_generator.py` includes debug prints:
- `[AI_DEBUG]` - API calls and tool execution
- `[AI_ERROR]` - Error responses

### View ChromaDB Data
```python
from backend.vector_store import VectorStore

vector_store = VectorStore('./chroma_db', 'all-MiniLM-L6-v2')
print(vector_store.course_catalog.get())  # Course metadata
print(vector_store.course_content.get())  # Content chunks
```

## Common Tasks

### Adding a New Test
1. Create file in `backend/tests/`
2. Follow naming pattern: `test_*.py`
3. Use pytest markers for categorization
4. Run: `uv run pytest backend/tests/your_test.py -v`

### Fixing Linting Issues
```bash
# Check what needs fixing
uv run flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503

# Fix automatically when possible
uv run black backend/ --line-length 100 --target-version py313

# Manual fixes for remaining issues
```

### Pre-commit Workflow
Before committing changes:
```bash
./format.sh
./check-quality.sh
```

This ensures:
- ✅ Code is properly formatted
- ✅ No linting errors
- ✅ All tests pass
- ✅ Ready for review

## CI/CD Integration

The quality scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run quality checks
  run: |
    uv pip install -e .[dev]
    ./format.sh
    ./check-quality.sh
```

## Troubleshooting

### Black not found
```bash
uv pip install black==24.10.0
```

### Linting false positives
Some rules can be disabled for specific lines:
```python
# noqa: E501 - line too long
# noqa: F401 - unused import
```

### Test failures
Run with verbose output:
```bash
uv run pytest backend/tests/ -v --tb=short
```

## References

- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [uv Documentation](https://docs.astral.sh/uv/)