#!/bin/bash

# Black formatter script for the RAG chatbot codebase
# Usage: ./format.sh

set -e

echo "🔍 Checking Python files to format..."

# Format all Python files in backend/ and root directory
uv run black backend/ main.py test_migration.py --line-length 100 --target-version py313

echo "✅ Formatting complete!"
echo ""
echo "📊 Summary:"
echo " - Line length: 100 characters"
echo " - Target version: Python 3.13"
echo " - Files formatted: backend/, main.py, test_migration.py"
