#!/bin/sh
# Validate in a temporary home, without a display or a session bus.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/home" "$tmp/config" "$tmp/cache" "$tmp/runtime"
env -i PATH=/usr/bin:/bin HOME="$tmp/home" LC_ALL=C.UTF-8 \
    XDG_CONFIG_HOME="$tmp/config" XDG_CACHE_HOME="$tmp/cache" \
    XDG_RUNTIME_DIR="$tmp/runtime" TMPDIR="$tmp" \
    sh "$root/tests/suite.sh" "$root" "$tmp"
