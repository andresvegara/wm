#!/bin/sh
# Exercise the real installer with synthetic payloads and no host services.
set -eu
root=$1
work=$2/awesome-package
fixture=$work/source
bin=$work/bin
dest=$work/destination
mkdir -p "$fixture/scripts" "$fixture/session" "$fixture/awesome/config" \
    "$fixture/awesome/widgets" "$bin" "$work/build" "$HOME/.config/awesome"
cp "$root/scripts/install.sh" "$root/scripts/dependencies.tsv" "$fixture/scripts/"
tab=$(printf '\t')
while IFS="$tab" read -r kind name package path; do
	[ "$kind" = awesome-command ] || continue
	printf '#!/bin/sh\nexit 0\n' > "$bin/$name"
	chmod 755 "$bin/$name"
done < "$fixture/scripts/dependencies.tsv"
for tool in sh find install stat cmp mkdir mktemp rm chmod tar cp; do
	ln -sf "/usr/bin/$tool" "$bin/$tool"
done
printf '#!/bin/sh\nprintf "1000\\n"\n' > "$bin/id"
chmod 755 "$bin/id"
for tool in sudo systemctl paru awesome picom dwmblocks; do
	printf '#!/bin/sh\nprintf "FORBIDDEN %%s\\n" "$0" >> "$FORBIDDEN_LOG"\nexit 99\n' > "$bin/$tool"
	chmod 755 "$bin/$tool"
done
export FORBIDDEN_LOG=$work/forbidden
export WM_OS_RELEASE=$work/os-release WM_RESOURCE_ROOT=$work/resources
mkdir -p "$WM_RESOURCE_ROOT/usr/lib/systemd/user"
while IFS="$tab" read -r kind name package path; do
	[ "$kind" = awesome-userunit ] || continue
	printf 'synthetic\n' > "$WM_RESOURCE_ROOT/usr/lib/systemd/user/$name"
done < "$fixture/scripts/dependencies.tsv"
printf 'ID=synthetic\n' > "$WM_OS_RELEASE"
printf '#!/bin/sh\n[ "${MOCK_GI_FAIL-0}" = 0 ]\n' > "$bin/python3"
printf '#!/bin/sh\ncase "$1" in --exists) [ "${MOCK_PC_FAIL-0}" = 0 ] ;; --variable=pc_path) printf "/synthetic/pkgconfig\\n" ;; esac\n' > "$bin/pkg-config"
printf '#!/bin/sh\n[ "${MOCK_CC_FAIL-0}" = 0 ] || exit 42\nwhile [ "$1" != -o ]; do shift; done\nprintf "synthetic helper\\n" > "$2"\n' > "$bin/cc"
printf '#!/bin/sh\n[ "$1" = -C ] && [ "$3" = ls-files ] || exit 99\nwhile IFS= read -r file; do printf "%%s\\n" "$file"; done < "$2/tracked"\n' > "$bin/git"
printf '#!/bin/sh\n[ "$1" = -C ] || exit 99\ncase "$3" in clean) exit 0 ;; CC=cc) ;; *) exit 99 ;; esac\n[ "${MOCK_MAKE_FAIL-0}" = 0 ] || exit 42\nfor file in dmenu stest; do printf "synthetic binary\\n" > "$2/$file"; done\n' > "$bin/make"
chmod 755 "$bin/python3" "$bin/pkg-config" "$bin/cc" "$bin/git" "$bin/make"
mkdir -p "$fixture/dmenu/.git"
printf '%s\n' Makefile config.def.h dmenu_path dmenu_run > "$fixture/dmenu/tracked"
for file in Makefile config.def.h dmenu_path dmenu_run; do
	printf 'synthetic dmenu source\n' > "$fixture/dmenu/$file"
done
for helper in wm-close wm-monitor; do
	printf '/* synthetic helper source, not compiled */\n' > "$fixture/awesome/$helper.c"
done
for file in awesome/rc.lua awesome/config/keys.lua awesome/widgets/init.lua awesome/widgets/backend.py; do
	printf '%s\n' '-- synthetic Lua payload, not executed' > "$fixture/$file"
done
for file in awesome-session awesome.desktop dunstrc; do
	printf 'synthetic %s\n' "$file" > "$fixture/session/$file"
done
for file in awesome-supervisor wm-command wm-launcher wm-run wm-control; do
	printf '#!/bin/sh\nexit 99 # synthetic, never executed\n' > "$fixture/scripts/$file"
done
printf 'personal config\n' > "$HOME/.config/awesome/rc.lua"
mkdir -p "$dest/usr/share/xsessions" "$dest/usr/local/share/xsessions"
printf 'dwm session\n' > "$dest/usr/share/xsessions/wm.desktop"
printf 'Plasma session\n' > "$dest/usr/local/share/xsessions/plasma.desktop"

fail()
{
	printf 'awesome package test: %s\n' "$*" >&2
	exit 1
}
run()
{
	env PATH="$bin" TMPDIR="$work/build" DESTDIR="${INSTALL_DEST-$dest}" \
	    sh "$fixture/scripts/install.sh" --awesome > "$work/output" 2>&1
}
reject()
{
	if run; then fail 'expected failure'; fi
	[ -z "$(find "$work/build" -mindepth 1 -print)" ] || fail 'leaked staging'
}
check()
{
	[ ! -e "$FORBIDDEN_LOG" ] || fail 'host command attempted'
	grep -qx 'personal config' "$HOME/.config/awesome/rc.lua" || fail 'personal rc changed'
	grep -qx 'dwm session' "$dest/usr/share/xsessions/wm.desktop" || fail 'dwm changed'
	grep -qx 'Plasma session' "$dest/usr/local/share/xsessions/plasma.desktop" || fail 'Plasma changed'
	[ -z "$(find "$work/build" -mindepth 1 -print)" ] || fail 'leaked staging'
}
run || { /usr/bin/tail -30 "$work/output"; fail 'initial staging'; }
check
for file in rc.lua config/keys.lua widgets/init.lua widgets/backend.py; do
	cmp "$fixture/awesome/$file" "$dest/usr/local/share/wm/awesome/$file"
	[ "$(stat -c %a "$dest/usr/local/share/wm/awesome/$file")" = 644 ] || fail 'Lua mode'
done
for file in awesome-session awesome-supervisor wm-command wm-launcher wm-run wm-control wm-close wm-monitor dmenu dmenu_path dmenu_run stest; do
	[ "$(stat -c %a "$dest/usr/local/bin/$file")" = 755 ] || fail 'executable mode'
done
cmp "$fixture/session/awesome.desktop" "$dest/usr/local/share/xsessions/awesome.desktop"
[ "$(stat -c %a "$dest/usr/local/share/xsessions/awesome.desktop")" = 644 ] || fail 'desktop mode'
[ ! -e "$dest/usr/local/share/wm/picom.conf" ] || fail 'picom installed'
[ ! -e "$dest/usr/local/bin/dwmblocks" ] || fail 'dwmblocks installed'
[ ! -e "$dest/usr/local/share/man" ] || fail 'manuals installed'
find "$dest" -type f -exec /usr/bin/stat -c '%n %i %Y %a' '{}' \; > "$work/before"
run || fail 'repeat staging'
grep -q '0 archivos Awesome actualizados' "$work/output" || fail 'not idempotent'
find "$dest" -type f -exec /usr/bin/stat -c '%n %i %Y %a' '{}' \; > "$work/after"
cmp "$work/before" "$work/after" || fail 'identical files rewritten'
chmod 600 "$dest/usr/local/share/wm/awesome/rc.lua"
run || fail 'mode repair'
[ "$(stat -c %a "$dest/usr/local/share/wm/awesome/rc.lua")" = 644 ] || fail 'mode not repaired'

# Every selected executable is checked before staging, without package actions.
while IFS="$tab" read -r kind name package path; do
	[ "$kind" = awesome-command ] || continue
	mv "$bin/$name" "$work/held-command"
	reject
	grep -Fq "$path" "$work/output" || fail "unchecked dependency: $name"
	mv "$work/held-command" "$bin/$name"
done < "$fixture/scripts/dependencies.tsv"
while IFS="$tab" read -r kind name package path; do
	[ "$kind" = awesome-userunit ] || continue
	mv "$WM_RESOURCE_ROOT/usr/lib/systemd/user/$name" "$work/held-unit"
	reject
	grep -Fq "$path" "$work/output" || fail "unchecked user unit: $name"
	mv "$work/held-unit" "$WM_RESOURCE_ROOT/usr/lib/systemd/user/$name"
done < "$fixture/scripts/dependencies.tsv"
MOCK_GI_FAIL=1; export MOCK_GI_FAIL
reject
unset MOCK_GI_FAIL
MOCK_PC_FAIL=1; export MOCK_PC_FAIL
reject
unset MOCK_PC_FAIL
MOCK_CC_FAIL=1; export MOCK_CC_FAIL
reject
unset MOCK_CC_FAIL
MOCK_MAKE_FAIL=1; export MOCK_MAKE_FAIL
reject
unset MOCK_MAKE_FAIL

# Missing source or special files must fail before changing any destination.
cp "$fixture/awesome/rc.lua" "$work/rc.good"
printf 'new Lua\n' > "$fixture/awesome/rc.lua"
mv "$fixture/scripts/wm-command" "$work/command.good"
reject
cmp "$work/rc.good" "$dest/usr/local/share/wm/awesome/rc.lua" || fail 'partial publication'
mv "$work/command.good" "$fixture/scripts/wm-command"
ln -s "$work/rc.good" "$fixture/awesome/widgets/linked.lua"
reject
rm "$fixture/awesome/widgets/linked.lua"
mkfifo "$fixture/awesome/widgets/pipe.lua"
reject
rm "$fixture/awesome/widgets/pipe.lua"

# Validate every destination before the first copy, including linked ancestors.
rm "$dest/usr/local/share/wm/awesome/config/keys.lua"
printf 'sentinel\n' > "$work/sentinel"
ln -s "$work/sentinel" "$dest/usr/local/share/wm/awesome/config/keys.lua"
reject
grep -qx sentinel "$work/sentinel" || fail 'symlink followed'
cmp "$work/rc.good" "$dest/usr/local/share/wm/awesome/rc.lua" || fail 'copied before preflight'
rm "$dest/usr/local/share/wm/awesome/config/keys.lua"
mv "$dest/usr/local/share/wm/awesome/config" "$work/config"
ln -s "$work/config" "$dest/usr/local/share/wm/awesome/config"
reject
rm "$dest/usr/local/share/wm/awesome/config"
mv "$work/config" "$dest/usr/local/share/wm/awesome/config"
run || fail 'repair after conflict'
check

# Real C builds in staging, still using synthetic configuration and no runtime apps.
for tool in cc as ld make pkg-config; do
	ln -sf "/usr/bin/$tool" "$bin/$tool"
done
git -C "$root/dmenu" ls-files > "$fixture/dmenu/tracked"
tar -cf "$work/dmenu-source.tar" -C "$root/dmenu" -T "$fixture/dmenu/tracked"
tar -xf "$work/dmenu-source.tar" -C "$fixture/dmenu"
cp "$root/awesome/wm-close.c" "$root/awesome/wm-monitor.c" "$fixture/awesome/"
run || { /usr/bin/tail -40 "$work/output"; fail 'real dmenu/helper build'; }
run || fail 'repeat real build'
grep -q '0 archivos Awesome actualizados' "$work/output" || fail 'real builds not idempotent'
check

# Package the delivered payloads too, not just files with the expected names.
cp "$root/awesome/rc.lua" "$fixture/awesome/rc.lua"
cp -R "$root/awesome/config/." "$fixture/awesome/config/"
cp -R "$root/awesome/widgets/." "$fixture/awesome/widgets/"
cp "$root/session/awesome-session" "$root/session/awesome.desktop" "$root/session/dunstrc" "$fixture/session/"
for file in awesome-supervisor wm-command wm-launcher wm-run wm-control; do
	cp "$root/scripts/$file" "$fixture/scripts/$file"
done
run || fail 'delivered payload staging'
for file in rc.lua widgets/init.lua widgets/backend.py config/keys.lua config/rules.lua config/layout.lua; do
	cmp "$root/awesome/$file" "$dest/usr/local/share/wm/awesome/$file"
done
grep -qx 'Exec=/usr/local/bin/awesome-session' "$dest/usr/local/share/xsessions/awesome.desktop"
grep -qx 'TryExec=/usr/local/bin/awesome-session' "$dest/usr/local/share/xsessions/awesome.desktop"
run || fail 'repeat delivered payload staging'
grep -q '0 archivos Awesome actualizados' "$work/output" || fail 'delivered payloads not idempotent'
check

# Non-DESTDIR copies are redirected only in this fixture; sudo is never real.
cp "$fixture/scripts/install.sh" "$work/install.good"
sed 's/target=$dest/target=$MOCK_DEST/' "$work/install.good" > "$fixture/scripts/install.sh"
export MOCK_DEST=$dest
printf '#!/bin/sh\n[ "$1:$2:$3:$4:$5:$6" = install:-D:-o:0:-g:0 ] || exit 99\nshift 6\nfor target; do :; done\ncase "$target" in "$MOCK_DEST"/*) ;; *) exit 99 ;; esac\nexec install -D "$@"\n' > "$bin/sudo"
chmod 755 "$bin/sudo"
# Treat existing files as non-root-owned to exercise ownership repair via sudo.
rm "$bin/stat"
printf '#!/bin/sh\nif [ "$1:$2" = -c:%%u:%%g ]; then printf "1000:1000\\n"; else exec /usr/bin/stat "$@"; fi\n' > "$bin/stat"
chmod 755 "$bin/stat"
INSTALL_DEST=; export INSTALL_DEST
run || fail 'simulated privileged copies'
check
mv "$bin/sudo" "$work/held-sudo"
reject
grep -q /usr/bin/sudo "$work/output" || fail 'missing sudo not diagnosed'
mv "$work/held-sudo" "$bin/sudo"
unset INSTALL_DEST
cp "$work/install.good" "$fixture/scripts/install.sh"

# Syntax is part of this test operation, never a stand-alone validation claim.
sh -n "$root/scripts/install.sh"
sh -n "$root/tests/awesome-package.sh"
printf '%s\n' 'PASS: Awesome package staging, modes, coexistence, idempotence, failures and symlinks; no host services'
