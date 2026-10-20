#!/bin/sh
# Build as the caller; elevate only the final file copies.
set -eu
umask 022

fail()
{
	printf 'install: %s\n' "$*" >&2
	exit 1
}

root=$(CDPATH= cd -- "${0%/*}/.." && pwd)
dest=${DESTDIR-}
case "$dest" in
'') ;;
/*) dest=${dest%/} ;;
*) fail 'DESTDIR debe ser una ruta absoluta' ;;
esac
command -v id >/dev/null 2>&1 || fail 'falta binario: /usr/bin/id'
[ "$(id -u)" != 0 ] || fail 'ejecuta como usuario normal, sin sudo; se pedirán permisos al copiar'
[ "$#" = 0 ] || fail 'uso: sh scripts/install.sh (DESTDIR opcional)'

arch=no
if [ -r "${WM_OS_RELEASE-/etc/os-release}" ]; then
	while IFS='=' read -r key value; do
		case "$key:$value" in
		ID:arch|ID:\"arch\"|ID:\'arch\') arch=yes ;;
		esac
	done < "${WM_OS_RELEASE-/etc/os-release}"
fi

missing()
{
	printf 'install: falta %s: %s\n' "$1" "$2" >&2
	case " $packages " in
	*" $package "*) ;;
	*) packages="$packages $package" ;;
	esac
}

check_dependencies()
{
	packages=
	tab=$(printf '\t')
	while IFS="$tab" read -r kind name package path; do
		case "$kind" in
		''|\#*) continue ;;
		command)
			command -v "$name" >/dev/null 2>&1 ||
			    missing binario "$path (buscado en PATH=$PATH)"
			;;
		pygi)
			if ! command -v python3 >/dev/null 2>&1 ||
			    ! python3 -c 'import sys; assert sys.version_info >= (3, 9); import gi; gi.require_version("Gio", "2.0"); from gi.repository import Gio' 2>/dev/null; then
				missing módulo "$path (requiere /usr/bin/python3 >= 3.9 y GIO)"
			fi
			;;
		pc)
			if ! command -v pkg-config >/dev/null 2>&1; then
				missing recurso "/usr/lib/pkgconfig/$path (no se pudo consultar /usr/bin/pkg-config)"
			elif ! pkg-config --exists "$name"; then
				paths=${PKG_CONFIG_LIBDIR-$(pkg-config --variable=pc_path pkg-config)}
				paths=${PKG_CONFIG_PATH-}:$paths
				oldifs=$IFS
				IFS=:
				for dir in $paths; do
					[ -z "$dir" ] || missing recurso "$dir/$path"
				done
				IFS=$oldifs
				[ -n "${paths#:}" ] || missing recurso "/usr/lib/pkgconfig/$path"
			fi
			;;
		font)
			family=
			if command -v fc-match >/dev/null 2>&1; then
				family=$(fc-match -f '%{family}' "$name") || family=
			fi
			case "$family" in
			*"$name"*) ;;
			*) missing fuente "$path (patrón Fontconfig: $name)" ;;
			esac
			;;
		*) fail "tipo de dependencia desconocido: $kind" ;;
		esac
	done < "$root/scripts/dependencies.tsv"
}

for project in dwm dmenu st; do
	[ -d "$root/$project/.git" ] || fail "falta checkout: $root/$project/.git"
done
check_dependencies
if [ -n "$packages" ]; then
	[ "$arch" = yes ] || fail 'dependencias ausentes; no se modificó el sistema'
	command -v paru >/dev/null 2>&1 || fail "falta binario: /usr/bin/paru (buscado en PATH=$PATH)"
	# Package names are fixed, whitespace-free entries from our manifest.
	paru -S --needed $packages || fail 'paru falló; instalación cancelada'
	check_dependencies
	[ -z "$packages" ] || fail 'siguen faltando dependencias después de paru'
fi
if [ -z "$dest" ]; then
	command -v sudo >/dev/null 2>&1 || fail "falta binario: /usr/bin/sudo (buscado en PATH=$PATH)"
fi
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
trap 'exit 1' HUP INT TERM
stage=$tmp/stage
mkdir -p "$stage/usr/local/bin" "$stage/usr/local/share/man/man1"
for project in dwm dmenu st; do
	mkdir "$tmp/$project"
	git -C "$root/$project" ls-files > "$tmp/files"
	tar -cf "$tmp/source.tar" -C "$root/$project" -T "$tmp/files"
	tar -xf "$tmp/source.tar" -C "$tmp/$project"
	(
		unset MAKEFLAGS MFLAGS
		make -C "$tmp/$project" clean
		rm -f "$tmp/$project/config.h"
		make -C "$tmp/$project" CC=cc PREFIX=/usr/local all
	)
	case "$project" in
	dwm) binaries=dwm; manuals=dwm ;;
	dmenu) binaries='dmenu dmenu_path dmenu_run stest'; manuals='dmenu stest' ;;
	st) binaries=st; manuals=st ;;
	esac
	for binary in $binaries; do
		install -m 755 "$tmp/$project/$binary" "$stage/usr/local/bin/$binary"
	done
	version=$(sed -n 's/^VERSION *= *//p' "$tmp/$project/config.mk")
	[ -n "$version" ] || fail "falta VERSION: $tmp/$project/config.mk"
	for manual in $manuals; do
		sed "s/VERSION/$version/g" "$tmp/$project/$manual.1" > "$stage/usr/local/share/man/man1/$manual.1"
	done
done
install -m 755 "$root/session/wm-session" "$stage/usr/local/bin/wm-session"
install -m 755 "$root/scripts/wm-launcher" "$stage/usr/local/bin/wm-launcher"
install -D -m 644 "$root/session/wm-st.desktop" "$stage/usr/local/share/applications/wm-st.desktop"
install -D -m 644 "$root/session/dwm-xdg-terminals.list" "$stage/usr/local/share/xdg-terminal-exec/dwm-xdg-terminals.list"
tic -sx -o "$stage/usr/local/share/terminfo" "$tmp/st/st.info"

find "$stage" -type f > "$tmp/install.files"
# Refuse destination symlinks before publishing any file.
while IFS= read -r source; do
	target=$dest${source#"$stage"}
	[ ! -L "$target" ] || fail "destino es un enlace simbólico: $target"
	[ ! -d "$target" ] || fail "destino es un directorio: $target"
done < "$tmp/install.files"

changed=0
while IFS= read -r source; do
	target=$dest${source#"$stage"}
	mode=$(stat -c %a "$source")
	if [ -f "$target" ] && cmp -s "$source" "$target" &&
	    [ "$(stat -c %a "$target")" = "$mode" ]; then
		if [ -n "$dest" ] || [ "$(stat -c %u:%g "$target")" = 0:0 ]; then
			continue
		fi
	fi
	if [ -n "$dest" ]; then
		install -D -m "$mode" "$source" "$target"
	else
		sudo install -D -o 0 -g 0 -m "$mode" "$source" "$target"
	fi
	changed=$((changed + 1))
done < "$tmp/install.files"
printf 'install: %s archivos actualizados; no se ha activado ninguna sesión\n' "$changed"
