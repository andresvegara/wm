#!/bin/sh
# Build only temporary source copies; never run the graphical executables.
set -eu

root=$1
tmp=$2
tab=$(printf '\t')

fail()
{
	printf 'test: %s\n' "$*" >&2
	exit 1
}

[ -z "${DISPLAY-}${WAYLAND_DISPLAY-}${DBUS_SESSION_BUS_ADDRESS-}" ] ||
    fail 'graphical/session environment is not isolated'

for sums in "$root"/patches/upstream/*/SHA256SUMS; do
	[ -f "$sums" ] || continue
	(cd "$(dirname "$sums")" && sha256sum --check SHA256SUMS)
done

git -C "$root" check-ignore -q .history-backups/ ||
    fail 'history backups must be ignored'

while IFS="$tab" read -r project url upstream revision tree; do
	case "$project" in
	dwm|dmenu|st) ;;
	*) fail "unknown project: $project" ;;
	esac
	git -C "$root/$project" merge-base --is-ancestor "$revision" HEAD ||
	    fail "$project: history does not contain the local import"
	[ "$(git -C "$root/$project" rev-list --max-parents=0 --all)" = "$revision" ] ||
	    fail "$project: history has an inherited or unexpected root"
	[ "$(git -C "$root/$project" rev-parse "$revision^{tree}")" = "$tree" ] ||
	    fail "$project: import differs from the original source tree"
	if git -C "$root/$project" cat-file -e "$upstream^{commit}" 2>/dev/null; then
		fail "$project: inherited upstream commit object is present"
	fi
	[ "$(git -C "$root/$project" remote)" = origin ] ||
	    fail "$project: unexpected remotes"
	git -C "$root" check-ignore -q "$project/" ||
	    fail "$project: source checkout is not ignored"
	[ -z "$(git -C "$root/$project" ls-files --others --exclude-standard)" ] ||
	    fail "$project: untracked files would be missing from exported patches"

	mkdir "$tmp/$project"
	git -C "$root/$project" archive "$revision" > "$tmp/$project.tar"
	tar -xf "$tmp/$project.tar" -C "$tmp/$project"
	if [ -f "$root/patches/$project/series" ]; then
		while IFS= read -r patch; do
			case "$patch" in
			''|\#*) continue ;;
			*/*|*..*) fail "$project: invalid patch filename" ;;
			esac
			patch --batch --dry-run -p1 -d "$tmp/$project" \
			    < "$root/patches/$project/$patch"
			git -C "$tmp/$project" apply --check \
			    "$root/patches/$project/$patch"
			git -C "$tmp/$project" apply \
			    "$root/patches/$project/$patch"
			# Rebuild config.h and every object after each feature patch.
			make -C "$tmp/$project" clean
			rm -f "$tmp/$project/config.h"
			make -C "$tmp/$project" all
			printf 'PASS: %s compiles after %s\n' "$project" "$patch"
		done < "$root/patches/$project/series"
	fi

	git -C "$root/$project" ls-files > "$tmp/$project.files"
	while IFS= read -r file; do
		cmp "$root/$project/$file" "$tmp/$project/$file" ||
		    fail "$project: export does not reproduce $file"
	done < "$tmp/$project.files"
	git -C "$root/$project" diff --check
	make -C "$tmp/$project" all
	printf 'PASS: %s base, patch reconstruction and build\n' "$project"
done < "$root/sources.tsv"

if [ -f "$root/checkouts.tsv" ]; then
	while IFS="$tab" read -r project url revision; do
		case "$project" in
		dwm|dmenu|st) ;;
		*) fail "unknown checkpoint project: $project" ;;
		esac
		[ "$(git -C "$root/$project" rev-parse HEAD)" = "$revision" ] ||
		    fail "$project: update checkouts.tsv after committing"
		[ "$(git -C "$root/$project" remote get-url origin)" = "$url" ] ||
		    fail "$project: origin differs from checkpoint"
	done < "$root/checkouts.tsv"
	printf '%s\n' 'PASS: local checkpoint revisions and publication destinations'
fi

cc -std=c99 -pedantic -Wall -Wno-deprecated-declarations \
    -D_DEFAULT_SOURCE -D_XOPEN_SOURCE=700 -DVERSION=\"6.8\" -DXINERAMA \
    -I"$tmp/dwm" $(pkg-config --cflags x11 xft xinerama) \
    "$root/tests/dwm-core.c" "$tmp/dwm/drw.o" "$tmp/dwm/util.o" \
    -o "$tmp/dwm-core-test" $(pkg-config --libs x11 xft xinerama) -lfontconfig
"$tmp/dwm-core-test"
cc -std=c99 -pedantic -Wall \
    -fsanitize=undefined -fno-sanitize-recover=all \
    -D_XOPEN_SOURCE=600 -DVERSION=\"0.9.3\" \
    -I"$tmp/st" $(pkg-config --cflags x11 xft) \
    "$root/tests/st-x.c" "$tmp/st/st.o" -o "$tmp/st-x-test" \
    $(pkg-config --libs x11 xft) -lfontconfig -lm -lutil
"$tmp/st-x-test"
cc -std=c99 -pedantic -Wall -fsanitize=address,undefined \
    -fno-sanitize-recover=all -D_XOPEN_SOURCE=600 -I"$tmp/st" \
    "$root/tests/st-core.c" -o "$tmp/st-core-test" -lm -lutil
ASAN_OPTIONS=detect_leaks=0 "$tmp/st-core-test"
sh "$root/tests/export-patches.sh" "$root" "$tmp"
sh "$root/tests/install.sh" "$root" "$tmp"

for file in "$root"/tests/*.sh "$root"/scripts/*.sh "$root/session/wm-session"; do
	[ -f "$file" ] || continue
	sh -n "$file"
done
printf '%s\n' 'PASS: shell syntax (part of the full test operation)'
printf '%s\n' 'PASS: isolated validation; no graphical program or service started'
