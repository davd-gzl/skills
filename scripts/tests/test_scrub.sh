#!/usr/bin/env bash
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
# Behaviour of scripts/scrub.sh over a scratch repository: a token, a private name
# and a person in a message refuse the push; a clean commit, a clean tree and
# SCRUB_SKIP pass; --push reads the hook's ref lines.
#
#   ./scripts/tests/test_scrub.sh
set -euo pipefail
here=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
names="$work/names.json"; printf '{"private_names": ["acme-internal", "someone"]}\n' > "$names"
repo="$work/repo"; mkdir -p "$repo/scripts"; cp "$here/scrub.sh" "$repo/scripts/"
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x SCRUB_NAMES="$names"
g() { git -C "$repo" "$@"; }
fake="ghp_$(printf 'A%.0s' $(seq 30))"   # a token shape built at run time, so this file carries none
pass=0; fail=0
check() { # name, expected exit, then the command, run inside the scratch repository
  local name=$1 want=$2; shift 2
  local got=0; (cd "$repo" && "$@") >"$work/out" 2>&1 || got=$?
  if [ "$got" = "$want" ]; then pass=$((pass + 1)); else fail=$((fail + 1)); printf 'FAIL %s: exit %s, wanted %s\n%s\n' "$name" "$got" "$want" "$(cat "$work/out")"; fi
}
expect_out() { grep -q -- "$1" "$work/out" || { fail=$((fail + 1)); printf 'FAIL output lacks %s:\n%s\n' "$1" "$(cat "$work/out")"; }; }
g init -q; printf 'clean line\n' > "$repo/a.md"; g add -A; g commit -qm base
check 'clean tree' 0 "$repo/scripts/scrub.sh" --tree
check 'clean first commit, nothing beyond a remote' 0 "$repo/scripts/scrub.sh"
printf 'token = "%s"\nsee acme-internal for the rest\nfine\n' "$fake" >> "$repo/a.md"; g add -A; g commit -qm 'leak, reviewed with someone'
check 'a leaking commit refuses' 1 "$repo/scripts/scrub.sh" HEAD~1..HEAD
expect_out 'secret shape: a.md'; expect_out 'private name: a.md'; expect_out 'private name: message'; expect_out '3 hit(s)'
check 'the whole tree refuses too' 1 "$repo/scripts/scrub.sh" --tree
check 'SCRUB_SKIP lets it through' 0 env SCRUB_SKIP=1 "$repo/scripts/scrub.sh" HEAD~1..HEAD
printf 'clean again\n' >> "$repo/a.md"; g add -A; g commit -qm clean
check 'a clean commit after the leak passes on its own range' 0 "$repo/scripts/scrub.sh" HEAD~1..HEAD
check '--push over the leaking range refuses' 1 bash -c "printf 'refs/heads/main %s refs/heads/main %s\n' \"\$(git -C '$repo' rev-parse HEAD)\" \"\$(git -C '$repo' rev-parse HEAD~2)\" | '$repo/scripts/scrub.sh' --push"
check '--push of a deleted branch is ignored' 0 bash -c "printf 'refs/heads/main 0000000000000000000000000000000000000000 refs/heads/main %s\n' \"\$(git -C '$repo' rev-parse HEAD)\" | '$repo/scripts/scrub.sh' --push"
check 'names file absent, secrets still refuse' 1 env SCRUB_NAMES=/nonexistent "$repo/scripts/scrub.sh" HEAD~2..HEAD~1
expect_out 'secret shape: a.md'; expect_out '1 hit(s)'
check 'names file absent, a private name alone passes' 0 env SCRUB_NAMES=/nonexistent bash -c "cd '$repo' && printf 'acme-internal only\n' >> a.md && git add -A && git commit -qm names && scripts/scrub.sh HEAD~1..HEAD"
printf 'untracked with %s\n' "$fake" > "$repo/new.md"
check '--tree reads an untracked file too' 1 "$repo/scripts/scrub.sh" --tree
expect_out 'secret shape: new.md'
rm "$repo/new.md"
check '--push with a remote sha this clone lacks scans what no remote holds' 1 bash -c "printf 'refs/heads/main %s refs/heads/main 1111111111111111111111111111111111111111\n' \"\$(git -C '$repo' rev-parse HEAD)\" | '$repo/scripts/scrub.sh' --push"
printf '%s passed, %s failed\n' "$pass" "$fail"; [ "$fail" = 0 ]
