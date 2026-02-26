#!/usr/bin/env bash
# Create a GitHub release with build artifacts.
#
# Usage:
#   ./scripts/release.sh v1.0.0              # tag a specific commit
#   ./scripts/release.sh v1.0.0 808491d      # tag a specific commit by SHA
#
# Prerequisites: gh CLI authenticated, python3 with build module installed.

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
TMPDIR=$(mktemp -d)
trap "git worktree remove '$TMPDIR' 2>/dev/null || rm -rf '$TMPDIR'" EXIT

git worktree add "$TMPDIR" "$TAG" --detach
(cd "$TMPDIR" && python3 -m build)

echo "==> Built artifacts:"
ls -la "$TMPDIR/dist/"

# Push the tag
git push origin "$TAG"

# Create the GitHub release
gh release create "$TAG" "$TMPDIR"/dist/* \
    --title "$TAG" \
    --generate-notes

echo "==> Release $TAG created successfully"
