#!/usr/bin/env bash
set -euo pipefail

OWNER="amittlearnings007"
DEFAULT_REPOSITORY="english-learning-companion-ai"
REPOSITORY_INPUT="${1:-$DEFAULT_REPOSITORY}"
BRANCH="${2:-main}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-Build English Learning Companion AI}"

if [[ "$REPOSITORY_INPUT" =~ ^https?://github\.com/([^/]+)/([^/]+)/?$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPOSITORY="${BASH_REMATCH[2]%.git}"
elif [[ "$REPOSITORY_INPUT" =~ ^https?://github\.com/([^/]+)/?$ ]]; then
  printf 'The supplied URL is a GitHub profile. Using default repository: %s/%s\n' "$OWNER" "$DEFAULT_REPOSITORY"
  REPOSITORY="$DEFAULT_REPOSITORY"
else
  REPOSITORY="${REPOSITORY_INPUT%.git}"
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init
fi

if [[ -z "$(git config user.name || true)" ]]; then
  git config user.name "$OWNER"
fi
if [[ -z "$(git config user.email || true)" ]]; then
  git config user.email "$OWNER@users.noreply.github.com"
fi

git config core.hooksPath .githooks
git branch -M "$BRANCH"
git add -A

if ! git diff --cached --quiet; then
  git commit -m "$COMMIT_MESSAGE"
else
  printf 'No new staged changes to commit.\n'
fi

REMOTE_URL="https://github.com/$OWNER/$REPOSITORY.git"

if command -v gh >/dev/null 2>&1; then
  if ! gh auth status >/dev/null 2>&1; then
    printf 'GitHub CLI is not authenticated. Run: gh auth login\n' >&2
    exit 1
  fi
  if ! gh repo view "$OWNER/$REPOSITORY" >/dev/null 2>&1; then
    gh repo create "$OWNER/$REPOSITORY" --public --source=. --remote=origin
  elif git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
  else
    git remote add origin "$REMOTE_URL"
  fi
else
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
  else
    git remote add origin "$REMOTE_URL"
  fi
  printf 'GitHub CLI is unavailable. Git will use your configured credential helper.\n'
fi

git push -u origin "$BRANCH"
printf 'Pushed to %s on branch %s.\n' "$REMOTE_URL" "$BRANCH"