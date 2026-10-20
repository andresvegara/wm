# wm

Entorno X11 en desarrollo basado en dwm, dmenu y st. No está activado ni listo
para sustituir Plasma.

## Estado

Preparados la estructura y la primera serie de dwm: flotante, un tag, foco por
clic, mitades/cuartos, maximizar/restaurar, fullscreen, centrar, traslado entre
monitores y cierre normal. `tests/dwm-core.c` prueba funciones reales con Xlib
simulado; no abre un display.

st incluye tamaño libre, transparencia, cursor parpadeante, perfil de Alacritty,
historial de 2000 filas y reflow al redimensionar, con tests simulados y ASan/UBSan.
Windows+Espacio abre el lanzador combinado de aplicaciones, archivos y acciones.
Siguen pendientes la bandeja y los componentes completos de sesión. Configurar fuentes emoji no
acredita todavía su renderizado. Hay avisos de funciones upstream sin uso tras
retirar sus atajos, no una compilación libre de warnings.

## Organización

- `dwm/`, `dmenu/`, `st/`: repositorios propios independientes, ignorados aquí.
- `sources.tsv`: proyecto, URL oficial, revisión oficial de procedencia,
  commit raíz local de importación y árbol original (cinco campos TSV).
- `checkouts.tsv`: destinos personales y HEAD locales del checkpoint.
- `patches/`: diffs exportados y orden de aplicación por proyecto.
- `scripts/`: exportador e instalador; `session/`: entorno local a dwm.
- `tests/`: validación aislada, sin conectarse a X11, Wayland o D-Bus.

El directorio físico sigue siendo `/home/kafka/dwm`; su repositorio raíz es
el coordinador. Cada checkout tiene un historial nuevo: un primer commit con
el código original y después solo sus commits locales por funcionalidad. No
hereda commits, ramas ni tags oficiales; conserva licencias y atribuciones.
Los .git anteriores están respaldados localmente en .history-backups/ e
ignorados por wm. El historial propio del coordinador no se reemplazó.

No hay submódulos. Clonar únicamente el coordinador no obtiene los tres
proyectos. sources.tsv relaciona procedencia e importaciones locales;
checkouts.tsv identifica los HEAD para retomar un checkpoint.

## Validación

```
make test
```

Verifica que cada importación es la única raíz de su historial y conserva el
árbol original, sin el commit oficial en el .git nuevo. Reconstruye las fuentes
más los parches, compila cada prefijo de serie y comprueba que el resultado
coincide con los checkouts. También prueba el exportador con cambios sintéticos.
Los tres proyectos se compilan en temporales. Los tests usan HOME temporal y
sin variables de sesión. El instalador se prueba con dependencias simuladas y
staging temporal; también empaqueta dos veces fuentes reales y comprueba su
idempotencia y terminfo. No instala en el sistema ni ejecuta programas gráficos.

Exportar una sola funcionalidad sobre la serie actual, sin crear commits:

```
make patch PROJECT=dwm FEATURE=nombre-funcionalidad
make test
```

El exportador no mezcla lo ya exportado ni sobrescribe parches existentes.
Las dependencias y el flujo están en [patches/README.md](patches/README.md).

Los nuevos archivos de un checkout deben incorporarse deliberadamente al
seguimiento de ese repositorio antes de exportarlos; el exportador rechaza
archivos untracked para no omitirlos silenciosamente.

## Instalador preparado

Desde la raíz, como usuario normal (sin anteponer sudo):

```sh
make install
# Si todavía falta make:
sh scripts/install.sh
```

**No se ha ejecutado la instalación real en esta fase.** El instalador prepara
solo lo existente: dwm, dmenu y st; no completa los servicios pendientes ni
registra o activa una sesión en el gestor de acceso.

- Instala binarios en `/usr/local/bin`, manuales en `/usr/local/share/man/man1`
  y terminfo en `/usr/local/share/terminfo`. Solo las copias finales usan sudo.
- Comprueba herramientas, bibliotecas, fuentes y programas de los atajos actuales
  (incluidos Brave, Chromium, Dolphin, Spotify y CopyQ). El inventario exacto
  está en `scripts/dependencies.tsv`.
- Solo con `ID=arch` instala dependencias ausentes mediante `paru -S --needed`,
  con sus confirmaciones normales. Puede incluir paquetes AUR: revisarlos antes
  de aceptarlos. No instala paru ni utiliza otro gestor. Fuera de Arch falla
  mostrando las rutas ausentes, no nombres de paquetes.
- Reconstruye copias temporales de los archivos versionados actuales; ignora
  config.h/objetos antiguos y archivos no versionados. Todos los builds terminan
  antes de publicar. No reescribe destinos con contenido/permisos correctos;
  una nueva ejecución actualiza archivos cambiados y corrige permisos.
- Un fallo de copia puede dejar una instalación parcial: corregir el error y
  repetir. No hay rollback automático ni eliminación de archivos obsoletos.
- `DESTDIR=/ruta/absoluta make install` prepara un árbol sin sudo. **No es un
  sandbox:** las dependencias y paru siguen siendo los del host.

El ejecutable instalado `wm-session` es el punto de entrada futuro de dwm:
selecciona **GTK3/4 Adwaita claro y Qt generic/Fusion claro**, incluido Qt Quick,
y añade el terminfo local a la búsqueda de ncurses conservando sus defaults.
Su entorno solo se hereda a dwm y sus descendientes: no escribe preferencias,
no cambia Plasma ni importa variables al bus. Iniciar dwm directamente no aplica
este entorno; st fuera de él puede necesitar
`TERMINFO_DIRS=/usr/local/share/terminfo:`.

No se garantiza el tema de GTK2, apps con apariencia propia, procesos ya abiertos,
sandboxes ni aplicaciones activadas por D-Bus fuera del árbol de dwm. No se ha
validado el aspecto visual.

Referencias: [paru](https://github.com/Morganamilo/paru),
[GTK](https://wiki.archlinux.org/title/GTK), [Qt](https://wiki.archlinux.org/title/Qt)
y [Fusion/Qt Quick](https://doc.qt.io/qt-6/qtquickcontrols-fusion.html).

## Lanzador

Windows+Espacio mezcla aplicaciones, nombres de archivos y acciones. GIO
interpreta las entradas .desktop; las etiquetas nunca se ejecutan como shell.
Las acciones de apagar/reiniciar/suspender/cerrar sesión requieren confirmación.
Las aplicaciones de terminal usan xdg-terminal-exec, con st como default de dwm.

El índice recorre HOME por nombres, sin leer contenido, ocultos, symlinks de
directorio ni carpetas de dependencias/build. Se renueva al invocar si tiene más
de 60 segundos; la primera búsqueda puede tardar en un HOME muy grande. Archivos
borrados o convertidos en symlinks no se abren desde un resultado obsoleto.
El índice está en `$XDG_CACHE_HOME/wm/files.json` (por defecto `~/.cache/wm`).
Shift+PageUp/PageDown y la rueda recorren el historial de st; aplicaciones que
solicitan eventos de ratón los conservan (Shift fuerza los atajos del terminal).

## Publicación futura

El coordinador wm tiene `origin` en `git@github.com:andresvegara/wm.git`.
En los checkouts, `origin` apunta también al repositorio del usuario:

- `dwm/`: `git@github.com:andresvegara/dwm.git`.
- `dmenu/`: `git@github.com:andresvegara/dmenu.git`.
- `st/`: `git@github.com:andresvegara/st.git`.

El usuario autorizó commits y pushes autónomos, con commits de una línea en
inglés y separados por funcionalidad. Los intentos de acceso SSH fueron
rechazados y el usuario pidió pausar todo acceso remoto hasta arreglarlo.
Por ahora los commits son exclusivamente locales; nada se considera publicado.
No usar git am ni force-push.

## Retomar en otro ordenador

**El checkpoint aún no está publicado.** Los commits de dwm y st son locales
mientras se resuelve SSH. dmenu solo tiene su commit propio de importación,
sin cambios funcionales ni commits vacíos.
Cuando se reanude el acceso, publicar primero los tres repositorios de fuentes
sin force-push y después wm, para que sus revisiones ya sean accesibles.

Después de publicar, clonar wm y, desde una copia nueva sin los checkouts:

```sh
set -eu
tab=$(printf '\t')
while IFS="$tab" read -r project url revision; do
    git clone "$url" "$project"
    git -C "$project" checkout --detach "$revision"
done < checkouts.tsv
make test
```

Las importaciones locales y los parches permiten reconstruir el código sin
necesitar los historiales oficiales. Los tests admiten commits descendientes
de cada raíz propia y exigen que importación + serie reproduzca exactamente
las fuentes. Los nombres de los parches conservan el hash oficial únicamente
para identificar su procedencia y compatibilidad.
Pendiente: bandeja, servicios y registro de sesión. No activar aún.

## Seguridad de la sesión actual

No ejecutar `make install` dentro de los proyectos, ni arrancar sus binarios,
compositores o servicios desde esta fase de desarrollo. No modificar la sesión
actual de Plasma, el autostart, las credenciales ni la configuración de acceso.
Las pruebas visuales, de energía, autenticación y hardware quedan para una fase
posterior expresamente autorizada.
