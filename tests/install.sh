#!/bin/sh
# Exercise the real installer with synthetic sources and a closed mock PATH.
set -eu
root=$1
work=$2/installer
fixture=$work/source\ tree
bin=$work/bin
dest=$work/destination\ tree
mkdir -p "$fixture/scripts" "$fixture/session" "$bin" "$work/build"
for file in "$root"/scripts/*; do
	[ ! -f "$file" ] || cp "$file" "$fixture/scripts/"
done
cp -R "$root/session/." "$fixture/session/"
cp "$root/checkouts.tsv" "$fixture/checkouts.tsv"
printf 'synthetic wallpaper resource\n' > "$fixture/wallpaper.png"
XDG_DATA_HOME=$work/user-data
export XDG_DATA_HOME
mkdir -p "$XDG_DATA_HOME/wm/dwm"
printf 'saved user choice\n' > "$XDG_DATA_HOME/wm/dwm/wallpaper"

fail()
{
	printf 'installer test: %s\n' "$*" >&2
	[ ! -f "$work/output" ] || /usr/bin/tail -35 "$work/output" >&2
	[ ! -f "$work/log" ] || /usr/bin/tail -20 "$work/log" >&2
	exit 1
}

# Every command not explicitly allowed below is a mock, including graphical apps.
tab=$(printf '\t')
while IFS="$tab" read -r kind name package path; do
	case "$kind" in command|awesome-command) ;; *) continue ;; esac
	printf '#!/bin/sh\nexit 0\n' > "$bin/$name"
	chmod 755 "$bin/$name"
done < "$root/scripts/dependencies.tsv"
for cmd in sh env tar cp rm mkdir mv mktemp cmp find sed grep tr head chmod; do
	ln -sf "/usr/bin/$cmd" "$bin/$cmd"
done
cat_mock()
{
	# The here-document is passed as stdin; never execute generated fixtures here.
	cp /dev/stdin "$bin/$1"
	chmod 755 "$bin/$1"
}
cat_mock id <<'MOCK'
#!/bin/sh
printf '%s\n' "${MOCK_UID-1000}"
MOCK
cat_mock git <<'MOCK'
#!/bin/sh
set -eu
[ "$1" = -C ] || exit 90
src=$2
shift 2
case "$1" in
init) mkdir "$src/.git" ;;
remote)
	case "$2" in
	add) case "$4" in https://github.com/*) ;; *) exit 91 ;; esac ;;
	set-url) ;;
	*) exit 90 ;;
	esac ;;
fetch)
	printf 'fetch %s\n' "$*" >> "$MOCK_LOG"
	[ "${MOCK_FETCH_FAIL-0}" = 0 ] || exit 46
	printf '%s\n' "$3" > "$src/revision"
	cp -R "$MOCK_STATE/bootstrap-source/." "$src/"
	;;
checkout) [ "${MOCK_CHECKOUT_FAIL-0}" = 0 ] ;;
rev-parse)
	if [ "${MOCK_WRONG_PIN-0}" = 1 ]; then printf wrong; else
		while IFS= read -r line; do printf '%s\n' "$line"; done < "$src/revision"
	fi ;;
ls-files) while IFS= read -r file; do printf '%s\n' "$file"; done < "$src/tracked" ;;
*) exit 90 ;;
esac
MOCK
cat_mock make <<'MOCK'
#!/bin/sh
set -eu
[ "$1" = -C ] || exit 90
src=$2
shift 2
printf 'make %s %s\n' "${src##*/}" "$*" >> "$MOCK_LOG"
case "$*" in
clean) exit 0 ;;
'CC=cc PREFIX=/usr/local all') ;;
*) exit 90 ;;
esac
[ ! -f "$src/config.h" ] || [ "${src##*/}" = dwmblocks ] || exit 91
[ "${MOCK_MAKE_FAIL-}" != "${src##*/}" ] || exit 42
case "${src##*/}" in
dwm) outputs=dwm ;;
dmenu) outputs='dmenu stest' ;;
st) outputs=st ;;
dwmblocks) outputs='dwmblocks wm-keyboard' ;;
*) exit 90 ;;
esac
for output in $outputs; do cp "$src/PAYLOAD" "$src/$output"; done
MOCK
cat_mock python3 <<'MOCK'
#!/bin/sh
[ "$1" = -c ] && [ "$2" = 'import sys; assert sys.version_info >= (3, 9)' ] && [ ! -f "$MOCK_STATE/python-version" ]
MOCK
cat_mock pkg-config <<'MOCK'
#!/bin/sh
case "$1" in
--exists) [ ! -f "$MOCK_STATE/pc-$2" ] ;;
--variable=pc_path) printf '%s\n' "$MOCK_STATE/pc search:/virtual/lib/pkgconfig" ;;
--cflags|--libs) ;;
*) exit 90 ;;
esac
MOCK
cat_mock fc-match <<'MOCK'
#!/bin/sh
if [ -f "$MOCK_STATE/font" ]; then printf Fallback; else printf '%s' "$3"; fi
MOCK
cat_mock tic <<'MOCK'
#!/bin/sh
set -eu
printf 'tic\n' >> "$MOCK_LOG"
[ "${MOCK_TIC_FAIL-0}" = 0 ] || exit 43
[ "$1" = -sx ] && [ "$2" = -o ] || exit 90
mkdir -p "$3/s"
printf 'synthetic terminfo\n' > "$3/s/st-256color"
MOCK
cat_mock install <<'MOCK'
#!/bin/sh
set -eu
for target; do :; done
case "$target" in
"$MOCK_DEST"/*)
	printf 'publish %s\n' "$target" >> "$MOCK_LOG"
	[ "${MOCK_INSTALL_FAIL-0}" = 0 ] || exit 44
	if [ -n "${MOCK_INSTALL_FAIL_AFTER-}" ]; then
		count=0
		[ ! -f "$MOCK_STATE/copies" ] || read -r count < "$MOCK_STATE/copies"
		[ "$count" -lt "$MOCK_INSTALL_FAIL_AFTER" ] || exit 44
		printf '%s\n' "$((count + 1))" > "$MOCK_STATE/copies"
	fi
	;;
esac
exec /usr/bin/install "$@"
MOCK
cat_mock paru <<'MOCK'
#!/bin/sh
set -eu
[ "$(id -u)" != 0 ] || exit 91
[ "$1" = -S ] && [ "$2" = --needed ] || exit 90
printf 'paru %s\n' "$*" >> "$MOCK_LOG"
[ "${MOCK_PARU_FAIL-0}" = 0 ] || exit 45
[ "${MOCK_PARU_NOFIX-0}" = 0 ] || exit 0
rm -f "$MOCK_STATE/pc-xft" "$MOCK_STATE/font"
if [ ! -f "$MOCK_BIN/cc" ]; then
	printf '#!/bin/sh\nwhile [ "$1" != -o ]; do shift; done\nprintf "synthetic helper\\n" > "$2"\n' > "$MOCK_BIN/cc"
	/usr/bin/chmod 755 "$MOCK_BIN/cc"
fi
MOCK
cat_mock systemctl <<'MOCK'
#!/bin/sh
set -eu
[ "$1" = --system ] || exit 90
shift
case "$1" in
show)
	case "$2" in
	--property=LoadState) [ ! -f "$MOCK_STATE/unit-$4" ] && printf 'loaded\n' || printf 'not-found\n' ;;
	--property=Id) printf '%s\n' "${MOCK_DISPLAY_MANAGER-sddm.service}" ;;
	--property=ActiveState) printf '%s\n' "${MOCK_COMPETITOR_ACTIVE-inactive}" ;;
	*) exit 90 ;;
	esac ;;
list-unit-files|list-units)
	[ -z "${MOCK_COMPETITOR-}" ] || printf '%s disabled -\n' "$MOCK_COMPETITOR" ;;
is-enabled)
	case "$2" in
	sddm.service|NetworkManager.service)
		if [ -f "$MOCK_STATE/enabled-$2" ]; then printf 'enabled\n'; else printf '%s\n' "${MOCK_SERVICE_STATE-disabled}"; fi ;;
	*) printf '%s\n' "${MOCK_COMPETITOR_STATE-disabled}" ;;
	esac ;;
enable)
	[ "${MOCK_ALLOW_SUDO-0}" = 1 ] || exit 99
	printf 'enable %s\n' "$2" >> "$MOCK_LOG"
	[ "${MOCK_ENABLE_FAIL-0}" = 0 ] || exit 47
	printf enabled > "$MOCK_STATE/enabled-$2" ;;
*) printf 'FORBIDDEN systemctl %s\n' "$*" >> "$MOCK_LOG"; exit 99 ;;
esac
MOCK
cat_mock sudo <<'MOCK'
#!/bin/sh
set -eu
if [ "${MOCK_ALLOW_SUDO-0}" != 1 ]; then
	printf 'FORBIDDEN sudo\n' >> "$MOCK_LOG"
	exit 99
fi
case "$1" in
install)
	[ "$2:$3:$4:$5:$6" = -D:-o:0:-g:0 ] || exit 90
	shift 6
	exec install -D "$@" ;;
systemctl) exec "$@" ;;
*) exit 99 ;;
esac
MOCK
cat_mock stat <<'MOCK'
#!/bin/sh
if [ "${MOCK_ALLOW_SUDO-0}" = 1 ] && [ "$1:$2" = -c:%u:%g ]; then
	printf '0:0\n'
else
	exec /usr/bin/stat "$@"
fi
MOCK

for project in dwm dmenu st dwmblocks; do
	src=$fixture/$project
	mkdir -p "$src/.git"
	printf 'VERSION = 1.2\n' > "$src/config.mk"
	printf 'synthetic %s\n' "$project" > "$src/PAYLOAD"
	printf 'stale\n' > "$src/config.h"
	printf '%s\n' config.mk PAYLOAD config.h > "$src/tracked"
	if [ "$project" != dwmblocks ]; then
		printf 'synthetic template\n' > "$src/config.def.h"
		printf 'config.def.h\n' >> "$src/tracked"
	fi
	case "$project" in
	dwm) ;;
	dmenu)
		for file in dmenu_run dmenu_path; do
			printf '#!/bin/sh\nexit 0\n' > "$src/$file"
			printf '%s\n' "$file" >> "$src/tracked"
		done ;;
	st) printf 'synthetic source\n' > "$src/st.info"
		printf 'st.info\n' >> "$src/tracked" ;;
	esac
done

# The default stages Awesome too; all new payloads remain synthetic.
mkdir -p "$fixture/awesome/config" "$fixture/awesome/widgets"
cp "$root/awesome/rc.lua" "$fixture/awesome/"
cp -R "$root/awesome/config/." "$fixture/awesome/config/"
cp -R "$root/awesome/widgets/." "$fixture/awesome/widgets/"
for helper in wm-close wm-monitor; do
	printf '/* synthetic */\n' > "$fixture/awesome/$helper.c"
done
cp "$root/scripts/awesome-supervisor" "$root/scripts/wm-command" "$fixture/scripts/"

export MOCK_LOG=$work/log MOCK_STATE=$work MOCK_BIN=$bin MOCK_DEST=$dest
export WM_RESOURCE_ROOT=$work/resources
mkdir -p "$WM_RESOURCE_ROOT/usr/lib/systemd/user"
for unit in gnome-keyring-daemon.socket gnome-keyring-daemon.service gcr-ssh-agent.socket gcr-ssh-agent.service; do
	printf synthetic > "$WM_RESOURCE_ROOT/usr/lib/systemd/user/$unit"
done
while IFS="$tab" read -r kind name package path; do
	case "$kind" in resource|awesome-resource)
		mkdir -p "$WM_RESOURCE_ROOT${path%/*}"
		printf synthetic > "$WM_RESOURCE_ROOT$path" ;;
	esac
done < "$root/scripts/dependencies.tsv"
export WM_OS_RELEASE=$work/os-release
export DESTDIR=$dest
printf 'ID=other\n' > "$WM_OS_RELEASE"
run()
{
	: > "$MOCK_LOG"
	env PATH="$bin" TMPDIR="$work/build" sh "$fixture/scripts/install.sh" > "$work/output" 2>&1
}
reject()
{
	if run; then fail 'expected installer failure'; fi
	[ -z "$(find "$work/build" -mindepth 1 -print)" ] || fail 'temporary build leaked'
}
no_publish()
{
	if grep -q '^publish\|^FORBIDDEN\|^enable ' "$MOCK_LOG"; then fail 'unexpected publication/elevation'; fi
}

# Malformed checkpoint inventories fail before dependencies, Git or publication.
cp "$fixture/checkouts.tsv" "$work/checkouts.good"
for invalid in duplicate missing revision project; do
	case "$invalid" in
	duplicate) cp "$work/checkouts.good" "$fixture/checkouts.tsv"
		printf 'st\tgit@github.com:andresvegara/st.git\t%s\n' 19a49a0480ff0ff1cd49f0500137619c622f4f3f >> "$fixture/checkouts.tsv" ;;
	missing) printf '' > "$fixture/checkouts.tsv" ;;
	revision) printf 'st\thttps://example.invalid/st.git\tbad-pin\n' > "$fixture/checkouts.tsv" ;;
	project) printf '../escape\thttps://example.invalid/st.git\tbad\n' > "$fixture/checkouts.tsv" ;;
	esac
	reject
	[ ! -s "$MOCK_LOG" ] || fail 'invalid inventory triggered work'
done
cp "$work/checkouts.good" "$fixture/checkouts.tsv"

# Non-Arch, Arch derivatives and unknown OS never try a package manager.
rm "$bin/cc"
printf missing > "$work/pc-xft"
printf missing > "$work/font"
for os in other derivative unknown; do
	case "$os" in
	other) printf 'ID=other\n' > "$WM_OS_RELEASE" ;;
	derivative) printf 'ID=derivative\nID_LIKE=arch\n' > "$WM_OS_RELEASE" ;;
	unknown) rm "$WM_OS_RELEASE" ;;
	esac
	reject
	grep -q '/usr/bin/cc' "$work/output" || fail 'missing command path'
	grep -q "$work/pc search/xft.pc" "$work/output" || fail 'missing metadata path'
	grep -q '/usr/share/fonts/TTF/HackNerdFontMono-Regular.ttf' "$work/output" || fail 'missing font path'
	if grep -q 'gcc\|libxft\|ttf-hack-nerd' "$work/output"; then fail 'package names in diagnostics'; fi
	[ ! -s "$MOCK_LOG" ] || fail 'non-Arch attempted work'
done
printf 'ID="arch"\n' > "$WM_OS_RELEASE"
mv "$fixture/st/.git" "$fixture/st/absent-git"
reject
[ ! -s "$MOCK_LOG" ] || fail 'missing checkout triggered package installation'
grep -q 'falta checkout:' "$work/output" || fail 'missing checkout diagnostic'
mv "$fixture/st/absent-git" "$fixture/st/.git"
mv "$bin/paru" "$work/paru"
reject
grep -q /usr/bin/paru "$work/output" || fail 'missing paru path'
no_publish
mv "$work/paru" "$bin/paru"
MOCK_PARU_FAIL=1; export MOCK_PARU_FAIL
reject
no_publish
unset MOCK_PARU_FAIL
MOCK_PARU_NOFIX=1; export MOCK_PARU_NOFIX
reject
grep -q 'siguen faltando' "$work/output" || fail 'dependency recheck skipped'
no_publish
unset MOCK_PARU_NOFIX

# Arch repairs all missing dependencies in a single normal-user invocation.
run || { /usr/bin/tail -50 "$work/output"; fail 'Arch install'; }
[ "$(grep -c '^paru ' "$MOCK_LOG")" = 1 ] || fail 'more than one paru invocation'
grep -q 'paru -S --needed gcc libxft ttf-hack-nerd noto-fonts-emoji' "$MOCK_LOG" || fail 'wrong Arch packages'
[ -x "$dest/usr/local/bin/st" ] || fail 'missing executable'
[ -x "$dest/usr/local/bin/awesome-session" ] || fail 'default omitted Awesome'
[ -f "$dest/usr/local/share/wm/awesome/config/session.lua" ] || fail 'native session missing'
[ -f "$dest/usr/local/share/xsessions/awesome.desktop" ] || fail 'Awesome entry missing'
[ -x "$dest/usr/local/bin/wm-displays" ] || fail 'missing display manager'
[ -x "$dest/usr/local/bin/wm-run" ] || fail 'missing launch reporter'
[ -x "$dest/usr/local/bin/wm-control" ] || fail 'missing OSD controls'
cmp "$root/scripts/wm-control" "$dest/usr/local/bin/wm-control" || fail 'wrong OSD controls'
cmp "$root/scripts/wm-run" "$dest/usr/local/bin/wm-run" || fail 'wrong launch reporter'
[ ! -e "$dest/usr/local/share/wm/pulse-client.conf" ] || fail 'obsolete Pulse client config installed'
for helper in wm-appearance wm-notifications wm-lock wm-randr-watch wm-wallpaper; do
	[ -x "$dest/usr/local/bin/$helper" ] || fail "missing helper: $helper"
done
cmp "$root/scripts/wm-wallpaper" "$dest/usr/local/bin/wm-wallpaper" || fail 'wrong wallpaper helper'
cmp "$fixture/wallpaper.png" "$dest/usr/local/share/wm/wallpaper.png" || fail 'wrong default wallpaper'
[ "$(stat -c %a "$dest/usr/local/share/wm/wallpaper.png")" = 644 ] || fail 'wallpaper mode'
grep -qx 'saved user choice' "$XDG_DATA_HOME/wm/dwm/wallpaper" || fail 'user wallpaper overwritten'
cmp "$root/scripts/wm_session.py" "$dest/usr/local/bin/wm_session.py" || fail 'shared Python module missing'
cmp "$root/awesome/config/themes.json" "$dest/usr/local/share/wm/themes.json" || fail 'shared palette missing'
cmp "$root/scripts/wm-displays" "$dest/usr/local/bin/wm-displays" || fail 'wrong display manager'
[ -x "$dest/usr/local/bin/wm-session" ] || fail 'missing session wrapper'
[ "$(stat -c %a "$dest/usr/share/xsessions/wm.desktop")" = 644 ] || fail 'session desktop mode'
grep -qx 'Exec=/usr/local/bin/wm-session' "$dest/usr/share/xsessions/wm.desktop" || fail 'session desktop Exec'
grep -qx 'Type=Application' "$dest/usr/share/xsessions/wm.desktop" || fail 'session desktop type'
if grep -q '^Hidden=true\|^NoDisplay=true' "$dest/usr/share/xsessions/wm.desktop"; then fail 'hidden X11 session'; fi
[ -f "$dest/usr/local/share/terminfo/s/st-256color" ] || fail 'missing isolated terminfo'
[ ! -e "$dest/usr/local/share/man" ] || fail 'manuals installed'

# No default image is distributed; a clean install must still work.
mv "$fixture/wallpaper.png" "$work/wallpaper.good"
(
	export DESTDIR="$work/no-image" MOCK_DEST="$work/no-image"
	run || fail 'install without default wallpaper'
)
[ -x "$work/no-image/usr/local/bin/wm-wallpaper" ] || fail 'missing wallpaper selector without default'
[ ! -e "$work/no-image/usr/local/share/wm/wallpaper.png" ] || fail 'unexpected default wallpaper'
grep -qx 'saved user choice' "$XDG_DATA_HOME/wm/dwm/wallpaper" || fail 'user wallpaper touched without default'
# Invalid packaged defaults still fail before publication.
ln -s "$work/wallpaper.good" "$fixture/wallpaper.png"
reject
no_publish
rm "$fixture/wallpaper.png"
mv "$work/wallpaper.good" "$fixture/wallpaper.png"
grep -qx 'saved user choice' "$XDG_DATA_HOME/wm/dwm/wallpaper" || fail 'user wallpaper touched'

# An unrelated man directory symlink must not block or receive any writes.
mv "$dest" "$work/first-install"
mkdir -p "$dest/usr/local/share" "$work/manuals/man1"
printf 'untouched\n' > "$work/manuals/man1/sentinel"
ln -s "$work/manuals" "$dest/usr/local/share/man"
run || fail 'install with linked man directory'
[ -L "$dest/usr/local/share/man" ] || fail 'man symlink replaced'
[ "$(find "$work/manuals" -type f | /usr/bin/wc -l)" = 1 ] || fail 'manuals written through symlink'
grep -qx untouched "$work/manuals/man1/sentinel" || fail 'existing manual changed'
[ -x "$dest/usr/local/bin/wm-session" ] || fail 'session missing with linked man directory'
cmp "$fixture/session/wm.desktop" "$dest/usr/share/xsessions/wm.desktop" || fail 'SDDM entry missing with linked man directory'
[ -z "$(find "$work/build" -mindepth 1 -print)" ] || fail 'temporary build leaked'
if grep -q '^enable ' "$MOCK_LOG"; then fail 'DESTDIR enabled services'; fi

# Bootstrap is mocked: no real Git/network, and failed trees are never published.
cp -R "$fixture/st" "$work/bootstrap-source"
mv "$fixture/st" "$work/existing-st"
MOCK_FETCH_FAIL=1; export MOCK_FETCH_FAIL
reject
no_publish
[ ! -e "$fixture/st" ] || fail 'failed bootstrap published a checkout'
[ -z "$(find "$fixture" -maxdepth 1 -name '.bootstrap-*' -print)" ] || fail 'bootstrap leaked'
unset MOCK_FETCH_FAIL
MOCK_CHECKOUT_FAIL=1; export MOCK_CHECKOUT_FAIL
reject
no_publish
[ ! -e "$fixture/st" ] || fail 'failed checkout published a tree'
[ -z "$(find "$fixture" -maxdepth 1 -name '.bootstrap-*' -print)" ] || fail 'failed checkout leaked'
unset MOCK_CHECKOUT_FAIL
MOCK_WRONG_PIN=1; export MOCK_WRONG_PIN
reject
no_publish
[ ! -e "$fixture/st" ] || fail 'wrong pin published a checkout'
unset MOCK_WRONG_PIN
run || fail 'bootstrap install'
[ -d "$fixture/st/.git" ] || fail 'bootstrap checkout missing'
[ "$(grep -c '^fetch ' "$MOCK_LOG")" = 1 ] || fail 'existing checkout fetched'
run || fail 'repeat bootstrap install'
if grep -q '^fetch ' "$MOCK_LOG"; then fail 'existing checkout fetched again'; fi
rm -rf "$fixture/st"
mv "$work/existing-st" "$fixture/st"

# Every declared executable/pc module is actually checked, without package actions.
printf 'ID=other\n' > "$WM_OS_RELEASE"
printf '%s\n' 'UNTRUSTED=$(printf injected > "$MOCK_STATE/os-executed")' >> "$WM_OS_RELEASE"
while IFS="$tab" read -r kind name package path; do
	case "$kind" in
	command)
		mv "$bin/$name" "$work/held-command"
		reject
		grep -Fq "$path" "$work/output" || fail "unchecked command: $name"
		mv "$work/held-command" "$bin/$name"
		;;
	unit)
		printf missing > "$work/unit-$name"
		reject
		grep -Fq "$path" "$work/output" || fail "unchecked system unit: $name"
		rm "$work/unit-$name"
		;;
	userunit)
		mv "$WM_RESOURCE_ROOT/usr/lib/systemd/user/$name" "$work/held-unit"
		reject
		grep -Fq "$path" "$work/output" || fail "unchecked user unit: $name"
		mv "$work/held-unit" "$WM_RESOURCE_ROOT/usr/lib/systemd/user/$name"
		;;
	pc)
		printf missing > "$work/pc-$name"
		reject
		grep -Fq "$path" "$work/output" || fail "unchecked metadata: $name"
		rm "$work/pc-$name"
		;;
	*) continue ;;
	esac
	[ ! -s "$MOCK_LOG" ] || fail 'dependency failure triggered work'
done < "$root/scripts/dependencies.tsv"
[ ! -e "$work/os-executed" ] || fail 'os-release was executed as code'
printf old > "$work/python-version"
reject
grep -q 'requiere Python >= 3.9' "$work/output" || fail 'old Python accepted'
no_publish
rm "$work/python-version"

# Conflicts, masked required units and unknown system states abort before copies.
MOCK_DISPLAY_MANAGER=gdm.service; export MOCK_DISPLAY_MANAGER
reject
no_publish
unset MOCK_DISPLAY_MANAGER
for unit in lightdm.service systemd-networkd.socket connman.service dhcpcd@eth0.service netctl@wifi.service; do
	MOCK_COMPETITOR=$unit MOCK_COMPETITOR_STATE=enabled
	export MOCK_COMPETITOR MOCK_COMPETITOR_STATE
	reject
	no_publish
	MOCK_COMPETITOR_STATE=disabled MOCK_COMPETITOR_ACTIVE=active
	export MOCK_COMPETITOR_ACTIVE
	reject
	no_publish
	unset MOCK_COMPETITOR_ACTIVE
done
MOCK_COMPETITOR_STATE=unexpected
reject
no_publish
unset MOCK_COMPETITOR MOCK_COMPETITOR_STATE
MOCK_SERVICE_STATE=masked; export MOCK_SERVICE_STATE
reject
no_publish
unset MOCK_SERVICE_STATE

# The source tree and HOME remain untouched; repeated installs preserve inodes.
grep -q stale "$fixture/st/config.h" || fail 'modified source checkout'
find "$dest" -type f -exec /usr/bin/stat -c '%n %i %Y %a' '{}' \; > "$work/before"
run || fail 'repeat install'
no_publish
grep -q '0 archivos actualizados' "$work/output" || fail 'not idempotent'
find "$dest" -type f -exec /usr/bin/stat -c '%n %i %Y %a' '{}' \; > "$work/after"
cmp "$work/before" "$work/after" || fail 'identical files rewritten'

printf 'updated dwm\n' > "$fixture/dwm/PAYLOAD"
run || fail 'update install'
[ "$(grep -c '^publish ' "$MOCK_LOG")" = 1 ] || fail 'unnecessary update'
grep -q 'updated dwm' "$dest/usr/local/bin/dwm" || fail 'stale executable'
chmod 600 "$dest/usr/local/bin/dmenu"
run || fail 'repair permissions'
[ "$(/usr/bin/stat -c %a "$dest/usr/local/bin/dmenu")" = 755 ] || fail 'permissions not repaired'

# Failures before publishing leave all final files intact.
mv "$fixture/awesome/rc.lua" "$work/awesome-rc"
reject
no_publish
mv "$work/awesome-rc" "$fixture/awesome/rc.lua"
MOCK_MAKE_FAIL=st; export MOCK_MAKE_FAIL
reject
no_publish
unset MOCK_MAKE_FAIL
MOCK_TIC_FAIL=1; export MOCK_TIC_FAIL
reject
no_publish
unset MOCK_TIC_FAIL
printf 'do not overwrite\n' > "$work/sentinel"
rm "$dest/usr/local/bin/st"
ln -s "$work/sentinel" "$dest/usr/local/bin/st"
reject
no_publish
grep -q 'enlace simbólico' "$work/output" || fail 'symlink accepted'
grep -q 'do not overwrite' "$work/sentinel" || fail 'symlink target changed'
rm "$dest/usr/local/bin/st"
MOCK_INSTALL_FAIL=1; export MOCK_INSTALL_FAIL
reject
unset MOCK_INSTALL_FAIL
run || fail 'resume after failed copy'

# Ancestor symlinks and non-directories also fail before any final copy.
mv "$dest/usr/local/bin" "$work/held-bin"
ln -s "$work/held-bin" "$dest/usr/local/bin"
reject
no_publish
grep -q 'enlace simbólico' "$work/output" || fail 'ancestor symlink accepted'
rm "$dest/usr/local/bin"
printf blocked > "$dest/usr/local/bin"
reject
no_publish
rm "$dest/usr/local/bin"
mv "$work/held-bin" "$dest/usr/local/bin"

# A mid-publication failure may leave a partial update; repeating repairs it.
printf 'second dwm\n' > "$fixture/dwm/PAYLOAD"
printf 'second dmenu\n' > "$fixture/dmenu/PAYLOAD"
MOCK_INSTALL_FAIL_AFTER=1; export MOCK_INSTALL_FAIL_AFTER
reject
[ "$(grep -c '^publish ' "$MOCK_LOG")" = 2 ] || fail 'mid-copy failure not exercised'
unset MOCK_INSTALL_FAIL_AFTER
run || fail 'repair partial publication'
grep -q 'second dwm' "$dest/usr/local/bin/dwm" || fail 'partial dwm not repaired'
grep -q 'second dmenu' "$dest/usr/local/bin/dmenu" || fail 'partial dmenu not repaired'
run || fail 'repeat repaired publication'
no_publish

MOCK_UID=0; export MOCK_UID
reject
[ ! -s "$MOCK_LOG" ] || fail 'root performed work'
unset MOCK_UID
for DESTDIR in relative / ///; do
	reject
	[ ! -s "$MOCK_LOG" ] || fail 'invalid DESTDIR triggered work'
done
DESTDIR=$dest
# Missing sudo is diagnosed before any real destination is inspected.
mv "$bin/sudo" "$work/sudo"
DESTDIR=
reject
grep -q /usr/bin/sudo "$work/output" || fail 'missing sudo path'
no_publish
DESTDIR=$dest
mv "$work/sudo" "$bin/sudo"

# Non-staging privilege/service paths, remapped ONLY inside the test fixture.
# Real target inspection/copies remain inside the synthetic destination tree.
cp "$fixture/scripts/install.sh" "$work/install.original"
sed 's/target=$dest/target=$MOCK_DEST/' "$work/install.original" > "$fixture/scripts/install.sh"
DESTDIR=
MOCK_ALLOW_SUDO=1; export MOCK_ALLOW_SUDO
run || { /usr/bin/tail -30 "$work/output"; fail 'privileged copies'; }
if grep -q '^enable \|^FORBIDDEN' "$MOCK_LOG"; then fail 'service mutation'; fi
run || fail 'repeat privileged copies'
no_publish
unset MOCK_ALLOW_SUDO
DESTDIR=$dest
cp "$work/install.original" "$fixture/scripts/install.sh"
[ -x "$dest/usr/local/bin/wm-supervisor" ] || fail 'supervisor not packaged'
[ ! -e "$dest/usr/local/share/wm/tint2rc" ] || fail 'obsolete tray config packaged'
for config in dunstrc picom.conf rofi.rasi; do
	cmp "$fixture/session/$config" "$dest/usr/local/share/wm/$config" || fail 'session defaults'
	[ "$(/usr/bin/stat -c %a "$dest/usr/local/share/wm/$config")" = 644 ] || fail 'session default mode'
done

# Test the wrapper's environment against a sibling fake supervisor, never X.
cat_mock unused <<'MOCK'
#!/bin/sh
set -eu
[ "$XDG_CURRENT_DESKTOP:$XDG_SESSION_DESKTOP:$DESKTOP_SESSION" = dwm:dwm:dwm ]
[ "${GTK_THEME-unset}:$QT_QPA_PLATFORMTHEME:$QT_STYLE_OVERRIDE:$QT_QUICK_CONTROLS_STYLE" = unset:generic:Fusion:Fusion ]
[ -z "${KDE_FULL_SESSION+x}${KDE_SESSION_VERSION+x}${QT_QUICK_CONTROLS_CONF+x}" ]
[ "$HOME:$XDG_CONFIG_HOME" = "$SESSION_HOME:$SESSION_CONFIG" ]
[ "$TERMINFO_DIRS" = "$SESSION_BINDIR/../share/terminfo:/custom/terminfo:" ]
[ "$#" = 2 ] && [ "$1" = 'argument with spaces' ] && [ "$2" = '*' ]
printf passed > "$SESSION_LOG"
MOCK
cp "$bin/unused" "$dest/usr/local/bin/wm-supervisor"
export GTK_THEME=Adwaita:dark QT_STYLE_OVERRIDE=breeze QT_QPA_PLATFORMTHEME=kde
export QT_QUICK_CONTROLS_STYLE=Material QT_QUICK_CONTROLS_CONF=/not/read
export KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 TERMINFO_DIRS=/custom/terminfo:
export SESSION_HOME=$HOME SESSION_CONFIG=$XDG_CONFIG_HOME
export SESSION_BINDIR=$dest/usr/local/bin SESSION_LOG=$work/session-result
sh "$dest/usr/local/bin/wm-session" 'argument with spaces' '*' || fail 'session environment'
[ "$(/usr/bin/head -c 6 "$SESSION_LOG")" = passed ] || fail 'fake supervisor not called'
[ "$GTK_THEME:$QT_STYLE_OVERRIDE:$QT_QPA_PLATFORMTHEME" = Adwaita:dark:breeze:kde ] || fail 'parent environment changed'
[ "$KDE_FULL_SESSION:$KDE_SESSION_VERSION:$QT_QUICK_CONTROLS_CONF" = true:6:/not/read ] || fail 'parent overrides changed'
unset GTK_THEME QT_STYLE_OVERRIDE QT_QPA_PLATFORMTHEME QT_QUICK_CONTROLS_STYLE
unset QT_QUICK_CONTROLS_CONF KDE_FULL_SESSION KDE_SESSION_VERSION TERMINFO_DIRS
printf '%s\n' 'PASS: installer dependencies, Arch/paru, staging, failures, idempotence and session-local appearance'

# Also package actual reconstructed sources with real build tools and tic.
# Runtime apps/fonts, OS detection and privilege escalation remain mocked.
for cmd in cc as ld make pkg-config tic; do
	ln -sf "/usr/bin/$cmd" "$bin/$cmd"
done
for project in dwm dmenu st dwmblocks; do
	source=$2/$project
	[ -d "$source" ] || source=$root/$project
	/usr/bin/git -C "$root/$project" ls-files > "$fixture/$project/tracked"
	tar -cf "$work/real-source.tar" -C "$source" -T "$fixture/$project/tracked"
	tar -xf "$work/real-source.tar" -C "$fixture/$project"
done
cp "$root/awesome/wm-close.c" "$root/awesome/wm-monitor.c" "$fixture/awesome/"
DESTDIR=$work/real\ destination
MOCK_DEST=$DESTDIR
printf 'ID=other\n' > "$WM_OS_RELEASE"
run || { /usr/bin/tail -60 "$work/output"; fail 'real staged build'; }
/usr/bin/infocmp -A "$DESTDIR/usr/local/share/terminfo" st-256color > "$work/terminfo"
grep -q 'st-256color' "$work/terminfo" || fail 'invalid compiled terminfo'
run || fail 'repeat real staged build'
no_publish
grep -q '0 archivos actualizados' "$work/output" || fail 'real binaries are not idempotent'
printf '%s\n' 'PASS: actual sources build/package twice without final rewrites; isolated st terminfo is readable'
