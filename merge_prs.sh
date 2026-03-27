#!/usr/bin/env bash
set -e

PRS=(11710 12673 12809 13161 13180 13247 13284 13286 13287 13290 13292 13293 13294 13350 13352 13446 13468 13485 13487 13511 13512 13513 13535 13576 13578 13580 13608 13660 13662 13697 13721 13726 13727 13732 13769 13785 13802 13805 13816)

for pr in "${PRS[@]}"; do
  ref="refs/pull/${pr}/head"
  echo "=== Merging PR #${pr} ==="
  if git merge --no-ff --no-edit -m "Merge upstream PR #${pr}" "$ref"; then
    echo "    OK"
  else
    conflicted=$(git diff --name-only --diff-filter=U | tr '\n' ' ')
    echo "    CONFLICTS: $conflicted"
    git add -A
    git commit -m "Merge upstream PR #${pr} (conflicts: $conflicted)"
  fi
done

echo "All PRs merged successfully."
