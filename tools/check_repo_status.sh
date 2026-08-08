#!/bin/bash
# check_repo_status.sh
# Added 2026-08-07 as part of bringing StudioYou onto the dev-session-protocol
# skill (same pattern SCREENBot uses). Run this at the close of every StudioYou
# session, from any tool, before the session is declared "closed" or "pushed."
#
# Checks every active repo in the StudioYou family, not just the one worked in.
# Exits non-zero and prints a loud failure if any repo is dirty or has
# untracked files. A repo that is committed-but-ahead-of-origin (push pending
# due to sandbox credential limitations) is reported separately and does NOT
# fail the check — that's expected, not a problem.

set -e

REPOS=(
  "/Users/supercreativepeople/Projects/studioyou-backend"
  "/Users/supercreativepeople/Projects/studioyou-fy-agent"
  "/Users/supercreativepeople/Downloads/studioyou-app"
  "/Users/supercreativepeople/Downloads/studioyou-site"
)

FAIL=0

for REPO in "${REPOS[@]}"; do
  if [ ! -d "$REPO/.git" ]; then
    echo "SKIP: $REPO is not a git repo"
    continue
  fi
  echo "=== $REPO ==="
  cd "$REPO"
  git fetch origin --quiet 2>/dev/null || echo "  WARN: could not fetch origin (auth or network)"
  STATUS=$(git status --short --branch)
  echo "$STATUS"

  if echo "$STATUS" | tail -n +2 | grep -qE '^\s?[MADRCU?]'; then
    echo "  FAIL: uncommitted or untracked changes present"
    FAIL=1
  fi
  if echo "$STATUS" | head -1 | grep -q '\[behind'; then
    echo "  FAIL: local branch is behind origin"
    FAIL=1
  fi
  if echo "$STATUS" | head -1 | grep -q '\[ahead'; then
    echo "  NOTE: local branch is ahead of origin — commits saved locally, push still pending"
  fi
  if ! echo "$STATUS" | head -1 | grep -q '\.\.\.origin/'; then
    echo "  WARN: no upstream tracking branch configured, cannot verify sync"
  fi
  echo ""
done

if [ "$FAIL" -eq 1 ]; then
  echo "REPO STATUS CHECK: FAILED. Do not declare this session closed."
  echo "Commit, push, and re-run before writing 'pushed' anywhere."
  exit 1
else
  echo "REPO STATUS CHECK: PASSED (clean trees; any ahead-of-origin repos just need a push)."
  exit 0
fi
