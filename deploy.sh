#!/usr/bin/env bash
# Publication is a separate, explicitly targeted operation. No default upstream, no force push.
set -euo pipefail
builtin cd "$(dirname "$0")"
: "${PUBLISH_REPO:?Set PUBLISH_REPO to your GitHub owner/repository after confirming redistribution permission}"
[[ "$PUBLISH_REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo 'Expected owner/repository' >&2; exit 1; }
[[ "$PUBLISH_REPO" != jankeesvw/* ]] || { echo 'Refusing upstream author destination' >&2; exit 1; }
[ -f site/index.html ] || { echo 'Run ./build.sh first' >&2; exit 1; }
remote="https://github.com/$PUBLISH_REPO.git"
if [ -n "$(git ls-remote --heads "$remote" gh-pages)" ]; then
  echo 'gh-pages already exists; refusing to replace history. Use a reviewed publication workflow.' >&2; exit 1
fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp -r site/. "$tmp/"
git -C "$tmp" init -q -b gh-pages
git -C "$tmp" add -A
git -C "$tmp" -c user.name="$(git config user.name)" -c user.email="$(git config user.email)" commit -q -m 'Publish Saiwai map'
git -C "$tmp" push "$remote" gh-pages
