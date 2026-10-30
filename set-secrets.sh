#!/usr/bin/env bash
# Set herald's posting secrets on every dadwritestech repo that exists on GitHub.
# Prompts for each value with input hidden; nothing is written to disk or shell history.
# Leave a prompt empty to skip that platform.
set -euo pipefail
OWNER=dadwritestech
REPOS="token-tax fineprint rejectall-index nerf-watch sitepatch reskin awesome-motion-md awesome-voice
one-file-saas necromancer agent-wrapped resurrect video-grep demo-to-code repo-saga babel-tv"

declare -A VAL
for name in HERALD_X_API_KEY HERALD_X_API_SECRET HERALD_X_ACCESS_TOKEN HERALD_X_ACCESS_SECRET \
            HERALD_BSKY_APP_PASSWORD HERALD_MASTODON_TOKEN; do
  read -rsp "$name (empty = skip): " v; echo
  VAL[$name]=$v
done
read -rp "HERALD_BSKY_HANDLE (e.g. name.bsky.social, empty = skip): " BSKY
read -rp "HERALD_MASTODON_URL (e.g. https://mastodon.social, empty = skip): " MASTO

for repo in $REPOS; do
  gh repo view "$OWNER/$repo" >/dev/null 2>&1 || { echo "skip $repo (not on GitHub yet)"; continue; }
  for name in "${!VAL[@]}"; do
    [ -n "${VAL[$name]}" ] && printf '%s' "${VAL[$name]}" | gh secret set "$name" -R "$OWNER/$repo" >/dev/null
  done
  [ -n "$BSKY" ] && gh variable set HERALD_BSKY_HANDLE -R "$OWNER/$repo" --body "$BSKY" >/dev/null
  [ -n "$MASTO" ] && gh variable set HERALD_MASTODON_URL -R "$OWNER/$repo" --body "$MASTO" >/dev/null
  echo "set $repo"
done
echo "Done. Re-run after each new repo goes on GitHub. Posting stays off until HERALD_ENABLED=true."
