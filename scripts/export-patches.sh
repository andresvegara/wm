#!/bin/sh
# Export one named feature on top of the existing series, without commits.
set -eu

project=${1-}
feature=${2-}
case "$project" in
dwm|dmenu|st|dwmblocks) ;;
*) printf '%s\n' 'usage: make patch PROJECT=dwm FEATURE=name' >&2; exit 1 ;;
esac
case "$feature" in
''|*[!a-z0-9-]*)
	printf '%s\n' 'export: feature must contain only a-z, 0-9 and hyphens' >&2
	exit 1
	;;
esac

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tab=$(printf '\t')
revision=
upstream=
while IFS="$tab" read -r name url source base tree; do
	if [ "$name" = "$project" ]; then
		upstream=$source
		revision=$base
	fi
done < "$root/sources.tsv"
[ -n "$revision" ] || { printf '%s\n' 'export: missing base' >&2; exit 1; }
git -C "$root/$project" merge-base --is-ancestor "$revision" HEAD || {
	printf 'export: %s history does not contain the recorded base\n' "$project" >&2
	exit 1
}
[ -z "$(git -C "$root/$project" ls-files --others --exclude-standard)" ] || {
	printf 'export: %s contains untracked files\n' "$project" >&2
	exit 1
}

short=$(printf '%.7s' "$upstream")
name="$project-$feature-$(date -u +%Y%m%d)-$short.diff"
dir="$root/patches/$project"
[ ! -e "$dir/$name" ] || {
	printf 'export: refusing to overwrite %s\n' "$name" >&2
	exit 1
}
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT HUP INT TERM

indexgit()
{
	GIT_INDEX_FILE="$tmp/index" git -C "$root/$project" "$@"
}

indexgit read-tree "$revision"
if [ -f "$dir/series" ]; then
	while IFS= read -r patch; do
		case "$patch" in
		''|\#*) continue ;;
		*/*|*..*) printf '%s\n' 'export: invalid patch filename' >&2; exit 1 ;;
		esac
		indexgit apply --cached --check "$dir/$patch"
		indexgit apply --cached "$dir/$patch"
	done < "$dir/series"
fi

# Include new, deliberately tracked source files without touching the real index.
git -C "$root/$project" ls-files > "$tmp/files"
while IFS= read -r file; do
	if [ -f "$root/$project/$file" ] &&
	    ! indexgit ls-files --error-unmatch -- "$file" >/dev/null 2>&1; then
		indexgit add --intent-to-add -- "$file"
	fi
done < "$tmp/files"
indexgit diff --check
if indexgit diff --quiet --; then
	printf '%s\n' 'export: no unexported changes' >&2
	exit 1
fi
indexgit diff --no-ext-diff --no-textconv --binary -- > "$tmp/feature.diff"
mkdir -p "$dir"
cp "$tmp/feature.diff" "$dir/$name"
printf '%s\n' "$name" >> "$dir/series"
printf 'export: %s\n' "$name"
