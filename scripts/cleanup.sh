#!/bin/bash
# Repository cleanup script for ReflectSonar
# Removes temporary files, build artifacts, and development files

echo "🧹 Cleaning up ReflectSonar repository..."

# Remove Python cache files
echo "  - Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove build artifacts
echo "  - Removing build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf src/*.egg-info/
rm -f *.spec

# Remove IDE files
echo "  - Removing IDE files..."
rm -rf .vscode/
rm -rf .idea/
rm -f *.swp *.swo

# Remove temporary files
echo "  - Removing temporary files..."
rm -f *.tmp *.temp
rm -f *.log

# Remove generated PDFs (keep examples if specifically named)
echo "  - Removing generated PDF files..."
rm -f test_report_*.pdf
rm -f reflect_sonar_report_*.pdf

# Remove OS specific files
echo "  - Removing OS specific files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

echo "✅ Repository cleanup completed!"
echo "📋 Files that will be committed:"
git status --porcelain 2>/dev/null || echo "  (Not a git repository or no changes)"