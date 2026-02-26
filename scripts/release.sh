#!/usr/bin/env bash
# Create a GitHub release with build artifacts.
#
# Usage:
#   ./scripts/release.sh v1.0.0              # tag HEAD
#   ./scripts/release.sh v1.0.0 808491d      # tag a specific commit by SHA
#
# Prerequisites: gh CLI authenticated, python3 available.

set -euo pipefail

TAG="${1:?Usage: $0 <tag> [commit]}"
COMMIT="${2:-HEAD}"

echo "==> Creating release $TAG at $COMMIT"

# Ensure we're on a clean checkout
if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: Working tree is dirty. Commit or stash changes first." >&2
    exit 1
fi

# Create the annotated tag
git tag -a "$TAG" "$COMMIT" -m "$TAG"

# Build from a temporary worktree at the tagged commit
BUILD_DIR=$(mktemp -d)
trap "git worktree remove '$BUILD_DIR' 2>/dev/null || rm -rf '$BUILD_DIR'" EXIT

git worktree add "$BUILD_DIR" "$TAG" --detach

# Create a venv and build inside it
python3 -m venv "$BUILD_DIR/.venv"
"$BUILD_DIR/.venv/bin/pip" install --quiet build
(cd "$BUILD_DIR" && "$BUILD_DIR/.venv/bin/python" -m build)

echo "==> Built artifacts:"
ls -la "$BUILD_DIR/dist/"

# Push the tag
git push origin "$TAG"

# Create the GitHub release
gh release create "$TAG" "$BUILD_DIR"/dist/* \
    --title "$TAG" \
    --generate-notes

echo "==> Release $TAG created successfully"
