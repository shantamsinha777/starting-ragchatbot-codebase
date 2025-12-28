#!/bin/bash

# Quality check script for the RAG chatbot codebase
# Runs black check, flake8 linting, and pytest
# Usage: ./check-quality.sh

set -e

echo "🧪 Running quality checks on RAG chatbot codebase..."
echo ""

# 1. Black format check
echo "1. Black format check"
if uv run black --check --line-length 100 --target-version py313 backend/ main.py test_migration.py 2>/dev/null; then
    echo "   ✅ All files are properly formatted"
else
    echo "   ❌ Some files need formatting. Run ./format.sh"
    exit 1
fi
echo ""

# 2. Flake8 linting
echo "2. Flake8 linting"
if command -v uv >/dev/null 2>&1 && uv run flake8 --version >/dev/null 2>&1; then
    uv run flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503
    echo "   ✅ No linting issues found"
else
    echo "   ⚠️  flake8 not installed. Run: uv pip install flake8"
fi
echo ""

# 3. Run tests if pytest is available
echo "3. Unit tests"
if command -v uv >/dev/null 2>&1 && uv run pytest --version >/dev/null 2>&1; then
    # Run tests if test files exist
    if [ -d "backend/tests" ]; then
        uv run pytest backend/tests/ -v --tb=short -q
        echo "   ✅ Tests completed"
    else
        echo "   ℹ️  No test directory found"
    fi
else
    echo "   ⚠️  pytest not installed. Run: uv pip install pytest"
fi
echo ""

echo "🎉 Quality checks completed successfully!"
echo ""
echo "Development workflow:"
echo "  ./format.sh        - Format all Python files"
echo "  ./check-quality.sh - Run all quality checks"
echo ""
echo "Quick install:"
echo "  uv pip install black flake8 pytest"
echo "  # OR"
echo "  uv pip install -e .[dev]"
