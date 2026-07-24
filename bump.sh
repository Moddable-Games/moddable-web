#!/bin/bash
# Bump version and propagate to all CSS/JS query strings
# Usage: ./bump.sh [major|minor|patch]

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION_FILE="$ROOT/version.txt"
CURRENT=$(cat "$VERSION_FILE" | tr -d '[:space:]')

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "${1:-patch}" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
  *) echo "Usage: $0 [major|minor|patch]"; exit 1 ;;
esac

NEW="$MAJOR.$MINOR.$PATCH"
echo "$NEW" > "$VERSION_FILE"
echo "Bumped: $CURRENT → $NEW"

# Rebuild to propagate version to all outputs
python3 "$ROOT/build/build.py"
echo "Build complete with version $NEW"
