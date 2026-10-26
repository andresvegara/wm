#!/bin/sh
# Compile source copies and exercise WM functions with Xlib substitutes only.
set -eu
root=$1
work=$2/external-build
mkdir -p "$work"
for project in dwm dwmblocks; do
	mkdir "$work/$project"
	git -C "$root/$project" ls-files > "$work/files"
	tar -cf "$work/source.tar" -C "$root/$project" -T "$work/files"
	tar -xf "$work/source.tar" -C "$work/$project"
	make -C "$work/$project" all
done
cc -std=c99 -pedantic -Wall -Wextra "$root/scripts/wm-randr-watch.c" -o "$work/wm-randr-watch" -lX11 -lXrandr
cc -std=c99 -pedantic -Wall -Wextra -fsanitize=address,undefined -fno-sanitize-recover=all \
    "$root/tests/randr-watch.c" -o "$work/randr-test"
"$work/randr-test"
cc -std=c99 -pedantic -Wall -Wno-deprecated-declarations \
    -fsanitize=address,undefined -fno-sanitize-recover=all \
    -D_DEFAULT_SOURCE -D_XOPEN_SOURCE=700 -DVERSION=\"6.8\" -DXINERAMA \
    -I"$work/dwm" $(pkg-config --cflags x11 xft xinerama xrandr) \
    "$root/tests/dwm-core.c" "$work/dwm/drw.o" "$work/dwm/util.o" \
    -o "$work/core" $(pkg-config --libs x11 xft xinerama xrandr) -lfontconfig
mkdir "$work/spawn-bin"
for tool in wm-run xmessage; do
	printf '#!/bin/sh\nprintf "%%s\\n" "$@" > "$WM_SPAWN_LOG"\n' > "$work/spawn-bin/$tool"
	chmod 755 "$work/spawn-bin/$tool"
done
WM_SPAWN_BIN="$work/spawn-bin" WM_SPAWN_LOG="$work/spawn.log" "$work/core"
cc -std=c99 -pedantic -Wall -fsanitize=address,undefined -fno-sanitize-recover=all \
    -I"$work/dwm" $(pkg-config --cflags x11 xft) \
    "$root/tests/dwm-draw.c" "$work/dwm/drw.o" "$work/dwm/util.o" \
    -o "$work/draw" $(pkg-config --libs x11 xft) -lfontconfig
"$work/draw"
mkdir "$work/lock-bin"
printf '#!/bin/sh\nprintf "%%s\\n" "$@" > "$WM_LOCK_LOG"\n' > "$work/lock-bin/loginctl"
chmod 755 "$work/lock-bin/loginctl"
env -i PATH="$work/lock-bin" XDG_SESSION_ID=synthetic WM_LOCK_LOG="$work/lock.log" /bin/sh "$root/scripts/wm-lock"
printf 'lock-session\n--\nsynthetic\n' > "$work/lock.expected"
cmp "$work/lock.expected" "$work/lock.log"
if env -i PATH="$work/lock-bin" WM_LOCK_LOG="$work/lock.log" /bin/sh "$root/scripts/wm-lock"; then
	echo 'test: missing session ID accepted' >&2
	exit 1
fi
cmp "$work/lock.expected" "$work/lock.log"
sh -n "$root/session/wm-session" "$root/scripts/wm-lock" "$root/scripts/install.sh" "$root/tests/dwm-external.sh"
