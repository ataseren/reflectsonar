#!/bin/bash
# Release script for ReflectSonar
# Creates a tagged release and pushes to GitHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if version is provided
if [ $# -eq 0 ]; then
    print_error "No version provided"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

VERSION="$1"
TAG_NAME="v${VERSION}"

# Validate version format (semantic versioning)
if [[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format. Use semantic versioning (e.g., 1.0.0)"
    exit 1
fi

print_status "Starting release process for version ${VERSION}"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    print_warning "You are not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Release cancelled"
        exit 1
    fi
fi

# Check if working directory is clean  
if [ -n "$(git status --porcelain)" ]; then
    print_error "Working directory is not clean. Please commit or stash your changes."
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^${TAG_NAME}$"; then
    print_error "Tag ${TAG_NAME} already exists"
    exit 1
fi

# Pull latest changes
print_status "Pulling latest changes..."
git pull origin main

# Run tests if they exist
if [ -f "requirements-dev.txt" ] || [ -d "tests" ]; then
    print_status "Running tests..."
    if command -v pytest &> /dev/null; then
        pytest
    else
        print_warning "pytest not found, skipping tests"
    fi
fi

# Build the binary
print_status "Building binary..."
python build_binary.py

if [ ! -f "dist/reflectsonar" ]; then
    print_error "Binary build failed - reflectsonar executable not found"
    exit 1
fi

print_success "Binary built successfully"

# Update version in files if needed
print_status "Updating version information..."

# Create or update VERSION file
echo "$VERSION" > VERSION

# If there's a setup.py or pyproject.toml, you might want to update version there too
# This is a placeholder for version updates in other files

# Create changelog entry if CHANGELOG.md exists
if [ -f "CHANGELOG.md" ]; then
    print_status "Please update CHANGELOG.md with release notes for version ${VERSION}"
    read -p "Press Enter when ready to continue..."
fi

# Commit version changes
if [ -n "$(git status --porcelain)" ]; then
    print_status "Committing version updates..."
    git add .
    git commit -m "Release version ${VERSION}"
fi

# Create and push tag
print_status "Creating and pushing tag ${TAG_NAME}..."
git tag -a "${TAG_NAME}" -m "Release version ${VERSION}"
git push origin main
git push origin "${TAG_NAME}"

print_success "Tag ${TAG_NAME} created and pushed successfully"

# Create GitHub release (if gh CLI is available)
if command -v gh &> /dev/null; then
    print_status "Creating GitHub release..."
    
    # Create release archive
    cd dist
    tar -czf "reflectsonar-${VERSION}-linux-x64.tar.gz" reflectsonar README.txt
    cd ..
    
    # Create the release
    gh release create "${TAG_NAME}" \
        --title "ReflectSonar ${VERSION}" \
        --generate-notes \
        "dist/reflectsonar-${VERSION}-linux-x64.tar.gz"
    
    print_success "GitHub release created successfully"
else
    print_warning "GitHub CLI (gh) not found. Please create the release manually on GitHub."
    print_status "Release archive created at: dist/reflectsonar-${VERSION}-linux-x64.tar.gz"
fi

# Cleanup
print_status "Cleaning up build artifacts..."
rm -rf build *.spec

print_success "Release ${VERSION} completed successfully!"
print_status "Next steps:"
echo "  1. Check the GitHub release page"
echo "  2. Update documentation if needed"
echo "  3. Announce the release"