#!/bin/sh
# Exercise feature exports in a disposable local clone, never a user checkout.
set -eu

root=$1
tmp=$2
fixture="$tmp/export-fixture"
mkdir -p "$fixture/scripts"
cp "$root/scripts/export-patches.sh" "$fixture/scripts/"
git clone -q --no-hardlinks --template= -- "$root/st" "$fixture/st"
revision=$(git -C "$fixture/st" rev-parse HEAD)
printf 'st\tfixture\t%s\n' "$revision" > "$fixture/sources.tsv"

fail()
{
	printf 'export test: %s\n' "$*" >&2
	exit 1
}

exportfeature()
{
	sh "$fixture/scripts/export-patches.sh" st "$1"
}

if exportfeature '' > "$tmp/expected-error" 2>&1; then
	fail 'missing feature accepted'
fi
if exportfeature '../escape' > "$tmp/expected-error" 2>&1; then
	fail 'path traversal accepted'
fi
[ ! -d "$fixture/patches" ] || fail 'invalid input created output'

printf '\n/* fixture-first */\n' >> "$fixture/st/config.def.h"
exportfeature first
printf '\n/* fixture-second */\n' >> "$fixture/st/config.def.h"
exportfeature second
[ "$(wc -l < "$fixture/patches/st/series")" -eq 2 ] ||
    fail 'two features did not produce two patches'

mkdir "$fixture/replayed"
git -C "$fixture/st" archive HEAD > "$tmp/export-base.tar"
tar -xf "$tmp/export-base.tar" -C "$fixture/replayed"
while IFS= read -r patch; do
	git -C "$fixture/replayed" apply "$fixture/patches/st/$patch"
	case "$patch" in
	st-second-*)
		if grep -q '^+/\* fixture-first' "$fixture/patches/st/$patch"; then
			fail 'second feature re-exported the first'
		fi
		;;
	esac
done < "$fixture/patches/st/series"
cmp "$fixture/replayed/config.def.h" "$fixture/st/config.def.h" ||
    fail 'series did not reproduce both changes'

if exportfeature third > "$tmp/expected-error" 2>&1; then
	fail 'empty patch accepted'
fi
printf '\n/* fixture-third */\n' >> "$fixture/st/config.def.h"
if exportfeature second > "$tmp/expected-error" 2>&1; then
	fail 'existing patch overwritten'
fi
[ "$(wc -l < "$fixture/patches/st/series")" -eq 2 ] ||
    fail 'failed export changed series'

# A deliberately tracked new file must be exported, without changing its index.
printf 'synthetic fixture\n' > "$fixture/st/new-file"
git -C "$fixture/st" add new-file
git -C "$fixture/st" diff --cached --binary > "$tmp/index-before"
exportfeature third
git -C "$fixture/st" diff --cached --binary > "$tmp/index-after"
cmp "$tmp/index-before" "$tmp/index-after" || fail 'real index changed'
while IFS= read -r patch; do
	case "$patch" in
	st-third-*) git -C "$fixture/replayed" apply "$fixture/patches/st/$patch" ;;
	esac
done < "$fixture/patches/st/series"
cmp "$fixture/replayed/new-file" "$fixture/st/new-file" ||
    fail 'new tracked file missing from export'
cmp "$fixture/replayed/config.def.h" "$fixture/st/config.def.h" ||
    fail 'third feature did not reproduce changes'
[ "$(git -C "$fixture/st" rev-parse HEAD)" = "$revision" ] ||
    fail 'export created a commit'
printf '%s\n' 'PASS: feature exports, replay, errors and index preservation'
