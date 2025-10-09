#!/bin/bash
# PyPI release script

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

echo "🚀 Starting PyPI release for version $VERSION"

# Update version in files
echo "$VERSION" > VERSION
sed -i "s/version = .*/version = \"$VERSION\"/" pyproject.toml
sed -i "s/__version__ = .*/__version__ = \"$VERSION\"/" src/reflectsonar/__init__.py

# Build package
./scripts/build_pypi.sh

echo "📤 Uploading to PyPI..."
python -m twine upload dist/*

echo "🏷️ Creating git tag..."
git add .
git commit -m "Release version $VERSION"
git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin main
git push origin "v$VERSION"

echo "✅ Release $VERSION completed successfully!"
