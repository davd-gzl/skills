#!/usr/bin/env bash
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
# Refuse a push of this public repository that adds a secret or a private name.
# Reads every line the pushed commits add and every commit message, or every
# tracked file with --tree, against the shapes a credential takes and the names
# the consumer's workspace.json lists under private_names, whole words, any
# case. Exit 1 on a hit, each printed as kind, file and line.
#
#   ./scripts/scrub.sh                what HEAD holds beyond every remote
#   ./scripts/scrub.sh <range>        those commits
#   ./scripts/scrub.sh --tree         every tracked file, for a first audit
#   ./scripts/scrub.sh --push         from the pre-push hook: ref lines on stdin
#
# SCRUB_NAMES names the json file, default ../workspace.json, the consumer that
# mounts this repository. SCRUB_SKIP=1 lets one push through after a line-by-line read.
set -euo pipefail
[ "${SCRUB_SKIP:-}" = 1 ] && exit 0
cd "$(git rev-parse --show-toplevel)"
self=scripts/scrub.sh
secrets='ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|Bearer [A-Za-z0-9._-]{20,}|(password|passwd|secret|token|api[_-]?key)[[:space:]]*[:=][[:space:]]*["'\''][^"'\'']{6,}'
names=''
file="${SCRUB_NAMES:-../workspace.json}"
# jq where the box has it, python3 otherwise: this repository is mounted on boxes carrying neither by default.
if [ -f "$file" ]; then
  if command -v jq >/dev/null 2>&1; then
    names=$(jq -r '.private_names // [] | join("|")' "$file")
  elif command -v python3 >/dev/null 2>&1; then
    names=$(python3 -c 'import json,sys; print("|".join(json.load(open(sys.argv[1])).get("private_names",[])))' "$file")
  else
    echo "scrub: neither jq nor python3 reads $file, so private names go unchecked" >&2; exit 1
  fi
fi
hits=$(mktemp); lines=$(mktemp); trap 'rm -f "$hits" "$lines"' EXIT

check() { # every line of $lines is "file: text"; a hit is appended to $hits with its kind
  grep -E "$secrets" "$lines" | sed 's/^/secret shape: /' >> "$hits" || true
  # An if, not a && list: under set -e a false test at the end of a function is the function's status, and the script dies on it.
  if [ -n "$names" ]; then grep -iE "\\<($names)\\>" "$lines" | sed 's/^/private name: /' >> "$hits" || true; fi
}
scan_tree() { # tracked files through git grep, untracked ones through grep, since a first audit runs before the add
  # Each grep may select nothing, which is exit 1 under pipefail, so each carries its own || true.
  {
    git grep -nI -e . -- . ":!$self" || true
    git ls-files --others --exclude-standard | grep -vx "$self" | xargs -r -d '\n' grep -HnI -e . || true
  } | sed 's/^\([^:]*:[^:]*\):/\1: /' > "$lines"
  check
}
scan_commits() { # the added lines of each commit's patch, then its message
  git log -p -U0 --no-color --format='commit %H' "$@" -- . ":!$self" | awk '
    /^commit / { commit = substr($0, 8, 9); next }
    /^\+\+\+ / { file = substr($0, 7); next }
    /^@@/ { next }
    /^\+/ { print file " (" commit "): " substr($0, 2) }' > "$lines"
  git log --format='message %h: %B' "$@" >> "$lines"
  check
}
case "${1:-}" in
  --tree) scan_tree ;;
  --push)
    while read -r _ local_sha _ remote_sha; do
      [ -n "$local_sha" ] || continue
      case "$local_sha" in 0000000000000000000000000000000000000000) continue ;; esac
      # A remote sha this clone has not fetched reads as unknown: scan what no remote holds instead.
      if [ "$remote_sha" != 0000000000000000000000000000000000000000 ] && git rev-parse -q --verify "$remote_sha^{commit}" >/dev/null 2>&1; then
        scan_commits "$remote_sha..$local_sha"
      else
        scan_commits "$local_sha" --not --remotes
      fi
    done ;;
  '') scan_commits HEAD --not --remotes ;;
  *) scan_commits "$1" ;;
esac
if [ -s "$hits" ]; then
  cat "$hits" >&2
  printf '%s hit(s): a secret or a private name never enters this public repository; SCRUB_SKIP=1 after a line-by-line read\n' "$(wc -l < "$hits")" >&2
  exit 1
fi
