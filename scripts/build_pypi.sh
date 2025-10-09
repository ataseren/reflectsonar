#!/bin/bash
# Build script for PyPI release

set -e

echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

echo "📦 Building package..."
python -m build

echo "🔍 Checking built package..."
python -m twine check dist/*

echo "✅ Package built successfully!"
echo "📋 Next steps:"
echo "   1. Test install: pip install dist/*.whl"
echo "   2. Upload to TestPyPI: python -m twine upload --repository testpypi dist/*"
echo "   3. Upload to PyPI: python -m twine upload dist/*"
