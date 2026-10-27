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
/*)
	while [ "${dest%/}" != "$dest" ]; do dest=${dest%/}; done
	[ -n "$dest" ] || fail 'DESTDIR no puede ser la raíz del sistema'
	;;
*) fail 'DESTDIR debe ser una ruta absoluta' ;;
esac
command -v id >/dev/null 2>&1 || fail 'falta binario: /usr/bin/id'
[ "$(id -u)" != 0 ] || fail 'ejecuta como usuario normal, sin sudo; se pedirán permisos al copiar'
session=all
case "$*" in
'') ;;
--awesome) [ "$#" = 1 ] || fail 'argumentos inválidos'; session=awesome ;;
*) fail 'uso: sh scripts/install.sh [--awesome] (DESTDIR opcional)' ;;
esac

publish()
{
	find "$stage" -type f > "$tmp/install.files"
	# Check every destination before the first privileged copy.
	while IFS= read -r source; do
		target=$dest${source#"$stage"}
		[ ! -L "$target" ] || fail "destino es un enlace simbólico: $target"
		[ ! -d "$target" ] || fail "destino es un directorio: $target"
		[ ! -e "$target" ] || [ -f "$target" ] || fail "destino no es un archivo: $target"
		parent=${target%/*}
		while [ -n "$parent" ]; do
			[ ! -L "$parent" ] || fail "directorio de destino es un enlace simbólico: $parent"
			[ ! -e "$parent" ] || [ -d "$parent" ] ||
			    fail "directorio de destino no es un directorio: $parent"
			parent=${parent%/*}
		done
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
}

stage_st()
{
	if [ ! -d "$tmp/st" ]; then
		source=$root/st
		if [ ! -d "$source/.git" ] && [ ! -f "$source/.git" ]; then
			source=$tmp/st-source
			tab=$(printf '\t')
			url= revision=
			while IFS="$tab" read -r project remote commit; do
				[ "$project" != st ] || { url=$remote; revision=$commit; }
			done < "$root/checkouts.tsv"
			case "$revision" in ''|*[!0-9a-f]*) fail 'revisión st inválida' ;; esac
			[ "${#revision}" = 40 ] || fail 'revisión st incompleta'
			case "$url" in
			git@github.com:*.git) url=https://github.com/${url#git@github.com:} ;;
			https://*) ;;
			*) fail 'bootstrap st requiere HTTPS' ;;
			esac
			git init -q "$source"
			GIT_TERMINAL_PROMPT=0 git -C "$source" fetch "$url" "$revision"
			git -C "$source" checkout --detach "$revision"
			[ "$(git -C "$source" rev-parse HEAD)" = "$revision" ] || fail 'revisión st incorrecta'
		fi
		mkdir "$tmp/st"
		git -C "$source" ls-files > "$tmp/st.files"
		tar -cf "$tmp/st.tar" -C "$source" -T "$tmp/st.files"
		tar -xf "$tmp/st.tar" -C "$tmp/st"
		(
			unset MAKEFLAGS MFLAGS
			make -C "$tmp/st" clean
			rm -f "$tmp/st/config.h"
			make -C "$tmp/st" CC=cc PREFIX=/usr/local all
		)
	fi
	install -D -m 755 "$tmp/st/st" "$stage/usr/local/bin/st"
	tic -sx -o "$stage/usr/local/share/terminfo" "$tmp/st/st.info"
	install -D -m 644 "$root/session/awesome-st.desktop" "$stage/usr/local/share/applications/awesome-st.desktop"
}

stage_awesome()
{
	# Own configuration only: never discover or overwrite a user's rc.lua.
	for file in scripts/wm_session.py awesome/config/drag.lua awesome/config/menu.lua awesome/config/health.lua awesome/widgets/aero.lua awesome/config/preferences.lua awesome/config/terminal.lua awesome/config/power-options.lua awesome/config/themes.json awesome/config/copyq.lua awesome/config/log.lua awesome/config/icons.lua awesome/config/power.lua awesome/config/power-settings.lua awesome/config/power-dbus.lua awesome/config/power-state.lua awesome/config/power-policy.lua awesome/rc.lua awesome/config/session.lua awesome/config/apps.lua awesome/config/applications.lua awesome/config/appearance.lua awesome/config/themes.lua awesome/config/titlebars.lua awesome/widgets/panel.lua awesome/widgets/notifications.lua awesome/wm-close.c awesome/config/picker.lua awesome/config/launcher.lua awesome/config/json.lua session/awesome-session session/awesome.desktop session/awesome-picom.conf session/awesome-xdg-terminals.list scripts/awesome-supervisor; do
		[ -f "$root/$file" ] && [ ! -L "$root/$file" ] || fail "falta archivo regular: $file"
	done
	[ -n "$dest" ] || command -v sudo >/dev/null 2>&1 || fail 'falta binario: /usr/bin/sudo'
	mkdir -p "$stage/usr/local/bin"
	for dir in config widgets; do
		[ -d "$root/awesome/$dir" ] && [ ! -L "$root/awesome/$dir" ] || fail "falta directorio regular: awesome/$dir"
		find "$root/awesome/$dir" -mindepth 1 ! -type d ! -type f > "$tmp/special"
		[ ! -s "$tmp/special" ] || fail "archivo especial en awesome/$dir"
		find "$root/awesome/$dir" -type f -name '*.lua' > "$tmp/lua.files"
		[ -s "$tmp/lua.files" ] || fail "sin módulos Lua: awesome/$dir"
		while IFS= read -r file; do
			install -D -m 644 "$file" "$stage/usr/local/share/wm/${file#"$root/"}"
		done < "$tmp/lua.files"
	done
	install -D -m 644 "$root/awesome/config/themes.json" "$stage/usr/local/share/wm/awesome/config/themes.json"
	install -D -m 644 "$root/awesome/config/themes.json" "$stage/usr/local/share/wm/themes.json"
	install -m 644 "$root/scripts/wm_session.py" "$stage/usr/local/bin/wm_session.py"
	stage_st
	if [ -e "$root/wallpaper.png" ] || [ -L "$root/wallpaper.png" ]; then
		[ -f "$root/wallpaper.png" ] && [ ! -L "$root/wallpaper.png" ] || fail 'wallpaper.png debe ser regular'
		install -D -m 644 "$root/wallpaper.png" "$stage/usr/local/share/wm/wallpaper.png"
	fi
	install -D -m 644 "$root/session/awesome-xdg-terminals.list" "$stage/usr/local/share/xdg-terminal-exec/awesome-xdg-terminals.list"
	for helper in wm-close; do
		cc -std=c99 -pedantic -Wall -Wextra $(pkg-config --cflags x11) \
		    "$root/awesome/$helper.c" -o "$stage/usr/local/bin/$helper" $(pkg-config --libs x11)
		chmod 755 "$stage/usr/local/bin/$helper"
	done
	install -D -m 644 "$root/session/awesome-picom.conf" "$stage/usr/local/share/wm/awesome-picom.conf"
	install -D -m 644 "$root/awesome/rc.lua" "$stage/usr/local/share/wm/awesome/rc.lua"
	install -m 755 "$root/session/awesome-session" "$stage/usr/local/bin/awesome-session"
	install -m 755 "$root/scripts/awesome-supervisor" "$stage/usr/local/bin/awesome-supervisor"
	for helper in wm-command wm-launcher wm-run wm-control wm-displays wm-wallpaper; do
		[ -f "$root/scripts/$helper" ] && [ ! -L "$root/scripts/$helper" ] || fail "falta helper regular: $helper"
		install -m 755 "$root/scripts/$helper" "$stage/usr/local/bin/$helper"
	done
	install -D -m 644 "$root/session/awesome.desktop" "$stage/usr/local/share/xsessions/awesome.desktop"
}

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
		case "$session:$kind" in
		awesome:awesome-*) kind=${kind#awesome-} ;;
		all:awesome-*) kind=${kind#awesome-} ;;
		awesome:*) continue ;;
		esac
		case "$kind" in
		''|\#*) continue ;;
		command)
			command -v "$name" >/dev/null 2>&1 ||
			    missing binario "$path (buscado en PATH=$PATH)"
			if [ "$name" = python3 ] && command -v python3 >/dev/null 2>&1 &&
			    ! python3 -c 'import sys; assert sys.version_info >= (3, 9)' 2>/dev/null; then
				missing binario "$path (requiere Python >= 3.9)"
			fi
			;;
		userunit)
			found=no
			for dir in /etc/systemd/user /usr/local/lib/systemd/user /usr/lib/systemd/user /lib/systemd/user; do
				[ ! -f "${WM_RESOURCE_ROOT-}$dir/$name" ] || found=yes
			done
			[ "$found" = yes ] || missing unidad "$path"
			;;
		unit)
			if ! command -v systemctl >/dev/null 2>&1 ||
			    [ "$(systemctl --system show --property=LoadState --value "$name" 2>/dev/null)" != loaded ]; then
				missing unidad "$path"
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
		resource)
			[ -f "${WM_RESOURCE_ROOT-}$path" ] || missing recurso "$path"
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

if [ "$session" = awesome ]; then
	check_dependencies
	if [ -n "$packages" ]; then
		[ -z "$dest" ] || fail 'dependencias Awesome ausentes; DESTDIR no modifica paquetes del sistema'
		[ "$arch" = yes ] || fail 'dependencias Awesome ausentes; no se modificó el sistema'
		command -v paru >/dev/null 2>&1 || fail "falta binario: /usr/bin/paru (buscado en PATH=$PATH)"
		paru -S --needed $packages || fail 'paru falló; instalación cancelada'
		check_dependencies
		[ -z "$packages" ] || fail 'siguen faltando dependencias después de paru'
	fi
	tmp=$(mktemp -d)
	trap 'rm -rf -- "$tmp"' EXIT
	trap 'exit 1' HUP INT TERM
	stage=$tmp/stage
	stage_awesome
	publish
	printf 'install: %s archivos Awesome actualizados; no se ha habilitado ni iniciado ningún servicio ni sesión\n' "$changed"
	exit 0
fi

# Validate the whole inventory before changing dependencies or fetching anything.
seen=' '
tab=$(printf '\t')
while IFS="$tab" read -r project url revision extra; do
	case "$project" in
	dwm|dmenu|st|dwmblocks) ;;
	*) fail "proyecto desconocido en checkouts.tsv: $project" ;;
	esac
	case "$seen" in
	*" $project "*) fail "checkout duplicado: $project" ;;
	esac
	seen="$seen$project "
	[ -z "$extra" ] || fail "campos adicionales en checkouts.tsv: $project"
	case "$revision" in
	''|*[!0-9a-f]*) fail "revisión inválida: $project" ;;
	esac
	[ "${#revision}" = 40 ] || fail "revisión incompleta: $project"
	[ -n "$url" ] || fail "falta URL: $project"
	if [ "$url" = - ]; then
		[ "$project" = dwmblocks ] || fail "destino pendiente no permitido: $project"
		[ -e "$root/$project" ] || fail "falta checkout dwmblocks; destino remoto pendiente de asignar"
	fi
done < "$root/checkouts.tsv"
for project in dwm dmenu st dwmblocks; do
	case "$seen" in
	*" $project "*) ;;
	*) fail "falta proyecto en checkouts.tsv: $project" ;;
	esac
	# Existing trees belong to the caller, including Git worktrees.
	if [ -e "$root/$project" ] || [ -L "$root/$project" ]; then
		[ -d "$root/$project/.git" ] || [ -f "$root/$project/.git" ] ||
		    fail "falta checkout: $root/$project/.git"
	fi
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
# Read-only checks, including staging: conflicts must precede every final copy.
# https://www.freedesktop.org/software/systemd/man/latest/systemctl.html
manager=$(systemctl --system show --property=Id --value display-manager.service) ||
    fail 'no se pudo consultar el gestor de acceso'
case "$manager" in
sddm.service|display-manager.service) ;;
*) fail "gestor de acceso competidor: $manager" ;;
esac
systemctl --system list-unit-files --type=service --type=socket --no-legend --no-pager > "$tmp/units" ||
    fail 'no se pudieron consultar las unidades instaladas'
systemctl --system list-units --all --type=service --type=socket --plain --no-legend --no-pager >> "$tmp/units" ||
    fail 'no se pudieron consultar las unidades activas'
while read -r unit rest; do
	case "$unit" in
	gdm.service|lightdm.service|lxdm.service|xdm.service|greetd.service|\
	systemd-networkd.service|systemd-networkd.socket|connman.service|\
	dhcpcd.service|dhcpcd@*.service|wicd.service|netctl.service|netctl@*.service|\
	netctl-auto@*.service|netctl-ifplugd@*.service) ;;
	*) continue ;;
	esac
	state=$(systemctl --system is-enabled "$unit" 2>/dev/null) || :
	case "$state" in
	enabled|enabled-runtime|alias) fail "servicio competidor habilitado: $unit" ;;
	disabled|static|indirect|masked|masked-runtime|linked|linked-runtime|generated|transient) ;;
	*) fail "estado desconocido de $unit: $state" ;;
	esac
	active=$(systemctl --system show --property=ActiveState --value "$unit") ||
	    fail "no se pudo consultar $unit"
	case "$active" in
	inactive|failed) ;;
	*) fail "servicio competidor activo: $unit ($active)" ;;
	esac
done < "$tmp/units"
for unit in sddm.service NetworkManager.service; do
	state=$(systemctl --system is-enabled "$unit" 2>/dev/null) || :
	case "$state" in
	enabled|disabled|enabled-runtime) ;;
	*) fail "estado no utilizable de $unit: $state" ;;
	esac
done
# Fetch into a sibling temporary directory, then publish only a verified tree.
# Git fetch/checkout semantics: https://git-scm.com/docs/git-fetch
bootstrap=
trap 'rm -rf -- "$tmp"; [ -z "$bootstrap" ] || rm -rf -- "$bootstrap"' EXIT
tab=$(printf '\t')
while IFS="$tab" read -r project url revision; do
	case "$project" in
	dwm|dmenu|st|dwmblocks) ;;
	*) fail "proyecto desconocido en checkouts.tsv: $project" ;;
	esac
	[ ! -e "$root/$project" ] && [ ! -L "$root/$project" ] || continue
	case "$url" in
	git@github.com:*.git) https=https://github.com/${url#git@github.com:} ;;
	https://*) https=$url ;;
	*) fail "bootstrap requiere HTTPS: $url" ;;
	esac
	bootstrap=$(mktemp -d "$root/.bootstrap-$project.XXXXXX")
	git -C "$bootstrap" init -q
	git -C "$bootstrap" remote add origin "$https"
	GIT_TERMINAL_PROMPT=0 git -C "$bootstrap" fetch origin "$revision" ||
	    fail "falló bootstrap HTTPS: $project"
	git -C "$bootstrap" checkout --detach "$revision"
	[ "$(git -C "$bootstrap" rev-parse HEAD)" = "$revision" ] ||
	    fail "revisión obtenida incorrecta: $project"
	git -C "$bootstrap" remote set-url origin "$url"
	[ ! -e "$root/$project" ] && [ ! -L "$root/$project" ] ||
	    fail "checkout apareció durante bootstrap: $project"
	mv -T -- "$bootstrap" "$root/$project"
	bootstrap=
done < "$root/checkouts.tsv"
stage=$tmp/stage
mkdir -p "$stage/usr/local/bin"
for project in dwm dmenu st dwmblocks; do
	mkdir "$tmp/$project"
	git -C "$root/$project" ls-files > "$tmp/files"
	tar -cf "$tmp/source.tar" -C "$root/$project" -T "$tmp/files"
	tar -xf "$tmp/source.tar" -C "$tmp/$project"
	(
		unset MAKEFLAGS MFLAGS
		make -C "$tmp/$project" clean
		if [ -f "$tmp/$project/config.def.h" ]; then
			rm -f "$tmp/$project/config.h"
		fi
		make -C "$tmp/$project" CC=cc PREFIX=/usr/local all
	)
	case "$project" in
	dwm) binaries=dwm ;;
	dmenu) binaries='dmenu dmenu_path dmenu_run stest' ;;
	st) binaries=st ;;
	dwmblocks) binaries='dwmblocks wm-keyboard' ;;
	esac
	for binary in $binaries; do
		install -m 755 "$tmp/$project/$binary" "$stage/usr/local/bin/$binary"
	done
done
[ -f "$root/scripts/wm-randr-watch.c" ] && [ ! -L "$root/scripts/wm-randr-watch.c" ] || fail 'falta helper RandR regular'
cc -std=c99 -pedantic -Wall -Wextra $(pkg-config --cflags x11 xrandr) \
    "$root/scripts/wm-randr-watch.c" -o "$stage/usr/local/bin/wm-randr-watch" $(pkg-config --libs x11 xrandr)
chmod 755 "$stage/usr/local/bin/wm-randr-watch"
install -m 755 "$root/session/wm-session" "$stage/usr/local/bin/wm-session"
install -m 755 "$root/scripts/wm-supervisor" "$stage/usr/local/bin/wm-supervisor"
for config in picom.conf dunstrc rofi.rasi; do
	install -D -m 644 "$root/session/$config" "$stage/usr/local/share/wm/$config"
done
if [ -e "$root/wallpaper.png" ] || [ -L "$root/wallpaper.png" ]; then
	[ -f "$root/wallpaper.png" ] && [ ! -L "$root/wallpaper.png" ] || fail 'wallpaper.png debe ser regular'
	install -D -m 644 "$root/wallpaper.png" "$stage/usr/local/share/wm/wallpaper.png"
fi
install -m 755 "$root/scripts/wm-launcher" "$stage/usr/local/bin/wm-launcher"
install -m 755 "$root/scripts/wm-run" "$stage/usr/local/bin/wm-run"
install -m 755 "$root/scripts/wm-control" "$stage/usr/local/bin/wm-control"
install -m 755 "$root/scripts/wm-status" "$stage/usr/local/bin/wm-status"
for helper in wm-appearance wm-notifications wm-lock wm-wallpaper; do
	[ -f "$root/scripts/$helper" ] && [ ! -L "$root/scripts/$helper" ] || fail "falta helper regular: $helper"
	install -m 755 "$root/scripts/$helper" "$stage/usr/local/bin/$helper"
done
install -m 755 "$root/scripts/wm-command" "$stage/usr/local/bin/wm-command"
install -m 755 "$root/scripts/wm-displays" "$stage/usr/local/bin/wm-displays"
install -D -m 644 "$root/session/wm.desktop" "$stage/usr/share/xsessions/wm.desktop"
install -D -m 644 "$root/session/wm-st.desktop" "$stage/usr/local/share/applications/wm-st.desktop"
install -D -m 644 "$root/session/dwm-xdg-terminals.list" "$stage/usr/local/share/xdg-terminal-exec/dwm-xdg-terminals.list"
tic -sx -o "$stage/usr/local/share/terminfo" "$tmp/st/st.info"

stage_awesome
publish
printf 'install: %s archivos actualizados (dwm y Awesome); no se ha habilitado ni iniciado ninguna sesión ni servicio\n' "$changed"
