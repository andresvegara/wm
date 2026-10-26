#!/bin/sh
# Validate in a temporary home, without a display or a session bus.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/home" "$tmp/config" "$tmp/cache" "$tmp/runtime"
chmod 700 "$tmp/home" "$tmp/config" "$tmp/cache" "$tmp/runtime"
case "${WM_TEST_SUITE-all}" in
all|dwm-external|awesome|awesome-power|awesome-copyq|awesome-terminal|awesome-picker) suite=$root/tests/suite.sh ;;
awesome-package) suite=$root/tests/awesome-package.sh ;;
dwm-package) suite=$root/tests/install.sh ;;
*) printf 'test: unknown WM_TEST_SUITE\n' >&2; exit 1 ;;
esac
env -i PATH=/usr/bin:/bin HOME="$tmp/home" LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 GIO_USE_VFS=local \
    XDG_CONFIG_HOME="$tmp/config" XDG_CACHE_HOME="$tmp/cache" \
    XDG_RUNTIME_DIR="$tmp/runtime" TMPDIR="$tmp" \
    sh "$suite" "$root" "$tmp" "${WM_TEST_SUITE-all}"
