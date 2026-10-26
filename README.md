# wm

Sesión X11 con dwm para ventanas/barra/bandeja y dwmblocks para indicadores.
Rofi proporciona aplicaciones, comandos, ventanas y menús; Dunst gestiona avisos,
historial y No molestar; Xfce Power Manager gestiona energía y xsettingsd la
apariencia. Bluebird es el tema predeterminado en dwm y Awesome. Alacritty es
la terminal; st y dmenu siguen incluidos como alternativas.

La [guía de sesión](docs/session.md) recoge atajos, componentes y límites.
Barra de dwm siempre visible abajo, con bandeja XEmbed y puente snixembed;
sin tint2 ni otro panel. Reloj y bandeja en el monitor principal, barra en todos;
fullscreen puede cubrirla. Inicio abre Rofi abajo a la izquierda; la barra muestra
un botón por ventana del monitor, incluidas minimizadas, sin tags ni layout.
Clic activa/restaura; clic en la activa minimiza. Titlebars dwm desactivadas por
config (`showtitlebar = 0`). Aplicaciones vía `.desktop` y acciones propias mediante
`~/.config/wm/dwm/menu.json`; ver la guía de sesión.
No se distribuye una imagen de fondo; sin elección guardada se usa el fondo liso
#f6f5f4. Puede aportarse un `wallpaper.png` local opcional, ignorado por Git.
«Fondo de pantalla» en Inicio/Acciones/menú de sesión abre Zenity (GTK4 en Arch);
feh aplica una imagen común a cada monitor en fill. La elección se copia y guarda
para restaurarla al entrar y al cambiar pantallas. No se usan Waypaper, Nitrogen,
Trayer ni GTK2 para estas funciones.
«Pantallas» usa Rofi y el backend xrandr/autorandr existente, con posiciones
relativas, perfiles y reversión independiente en 15 segundos. El watcher recibe
eventos RandR; no sondea pantallas en periodos estables. Combinaciones desconocidas
se notifican sin abrir menús automáticamente. Dwmblocks muestra batería, energía,
volumen, teclado, avisos y reloj; no necesita cbatticon ni pasystray ni añade un
servidor de audio. Energía se configura en la interfaz de Xfce Power Manager.

## Awesome

Sesión alternativa con configuración Lua propia, sin sustituir
Plasma/dwm ni activar nada. Sin argumentos, `sh scripts/install.sh` (o
`make install`) prepara dwm y Awesome; `sh scripts/install.sh --awesome` prepara
solo Awesome y componentes compartidos.
El instalador está preparado; las comprobaciones visuales y de hardware quedan
para la primera sesión. En Arch, `--awesome` resuelve sus paquetes con paru.
Awesome usa Alacritty como terminal predeterminada (también Super+Intro), controles de aplicaciones en
Lua y un selector de Apariencia Actual/Menta/Bluebird con elección privada persistente.
Bluebird se usa cuando no hay una elección guardada; sus recursos GTK/iconos son
opcionales y tienen fallback Adwaita, sin perder la paleta nativa.
Super+Espacio incluye Apariencia, Pantallas y aplicaciones en un selector nativo;
Super+D y el editor de monitores también usan UI de Awesome. `--awesome` ya no
requiere ni construye dmenu ni st; Alacritty se obtiene del paquete del sistema.
Las pruebas aisladas cubren el núcleo Lua, energía/almacenamiento, widgets,
supervisores y empaquetado; la suite completa incluye regresión dwm/dwmblocks.
No se ha probado una sesión gráfica real.
Ver [guía Awesome, validación y límites](docs/awesome.md).

## Instalar con el script

Desde esta carpeta, **como usuario normal**, sin anteponer sudo:

```sh
sh scripts/install.sh
# Equivalente: make install
```

- En Arch (`ID=arch`), usa `paru -S --needed` para dependencias ausentes,
  incluidas las de AUR: revisar sus confirmaciones. No instala paru.
  En otras distribuciones muestra recursos/rutas ausentes y aborta.
- Obtiene por HTTPS los checkouts ausentes, en las revisiones de `checkouts.tsv`.
  No reemplaza árboles existentes; construye sus archivos versionados actuales.
- Construye las variantes seleccionadas y prepara todos los archivos en temporales antes
  de publicar. Rechaza enlaces en destinos y directorios padres.
- Instala binarios y recursos de sesión, sin instalar manuales ni tocar
  `/usr/local/share/man` (aunque sea un enlace simbólico).
- Usa sudo solo para copias finales. Detecta gestores competidores antes de
  copiar y no los deshabilita. Nunca habilita/inicia/reinicia servicios ni cambia
  la sesión predeterminada.
- El instalador no escribe preferencias en HOME ni cambia PAM o políticas de
  energía. Al iniciar dwm se configura la integración de bloqueo/brillo en xfconf;
  las políticas energéticas se ajustan con Xfce Power Manager. No inicia ni habilita
  servicios de audio.
- Repetir actualiza solo archivos/permisos distintos. Un fallo durante copias
  puede dejar una instalación parcial: corregir y repetir.
- `DESTDIR=/ruta/absoluta sh scripts/install.sh` empaqueta sin sudo ni habilitar
  servicios. **No es un sandbox:** comprueba dependencias/servicios del host y en
  Arch puede ejecutar paru. `WM_OS_RELEASE` y `WM_RESOURCE_ROOT` se reservan para
  las simulaciones de tests; no usarlos en instalaciones normales.

Solo tras autorizar instalación y comprobaciones reales, guardar el trabajo,
cerrar la sesión actual y elegir **Awesome** o **wm** en SDDM. El instalador no
activa SDDM ni NetworkManager. No ejecutar otro gestor de ventanas encima del actual.

## Instalar los programas individualmente

Instalar previamente las dependencias de `scripts/dependencies.tsv` con el gestor
de la distribución. Compilar como usuario y ejecutar solo la instalación con sudo:

```sh
make -C dwm  && sudo make -C dwm PREFIX=/usr/local install
make -C dmenu && sudo make -C dmenu PREFIX=/usr/local install
make -C st   && sudo make -C st PREFIX=/usr/local install
```

Cada línea es independiente. Estos comandos upstream instalan el programa y sus
manuales; st también instala su terminfo. No instalan la sesión ni sus servicios.
Para un build limpio tras cambios de configuración, ejecutar antes
`make -C PROYECTO clean` y eliminar su `config.h` generado si se desea regenerarlo.

La **sesión completa** requiere además dwmblocks, wm-keyboard, el helper RandR,
el módulo Python compartido, paletas, configuraciones y supervisores. Usar
`scripts/install.sh` para prepararla íntegramente: copiar solo los ejecutables
upstream no instala esos componentes. Los destinos y modos exactos se mantienen
en ese script, evitando una segunda lista manual que pueda quedar incompleta.

Solo si **no hay otro gestor de acceso/red activo o habilitado**, habilitar para
próximos arranques (sin `--now`):

```sh
sudo systemctl enable sddm.service NetworkManager.service
```

La vía manual no tiene las protecciones del instalador. No deshabilitar un gestor
existente a ciegas: resolver el conflicto antes. El script es la vía recomendada.

## Destinos

| Contenido | Destino |
| --- | --- |
| Binarios y entrada de sesión | `/usr/local/bin` |
| Terminfo generado por el script | `/usr/local/share/terminfo` |
| Defaults de Dunst/Picom/Rofi y catálogo de temas | `/usr/local/share/wm` |
| Sesión X11 para SDDM | `/usr/share/xsessions/wm.desktop` |
| Entrada de st / selección de terminal | `/usr/local/share/applications`, `/usr/local/share/xdg-terminal-exec` |

`wm-session` aplica terminfo y el supervisor coordina Bluebird/Actual/Menta mediante
xsettingsd. La elección dwm persiste en `wm/dwm/appearance`, separada de Awesome;
se respetan elecciones existentes. XSettings afecta al display X y no garantiza
uniformidad para Qt, libadwaita, sandboxes ni aplicaciones con estilo propio. st fuera de la sesión puede necesitar
`TERMINFO_DIRS=/usr/local/share/terminfo:` si se instaló con el script.

## Validación

```sh
make test
```

Reconstruye cada prefijo de parches de dwm/dwmblocks/dmenu/st en temporales. Prueba
funciones reales dwm/st con Xlib simulado y ASan/UBSan, historial/reflow, bindings,
lanzador, supervisor, agentes, monitores, bloqueo e instalador con comandos
simulados. Empaqueta dos veces fuentes reales y comprueba idempotencia/terminfo.
No instala ni arranca programas gráficos, X, servicios o hardware reales.

**No se ha validado una sesión gráfica real**, autenticación, monitores, emoji
compuesto, secretos/VPN o audio. Persisten avisos upstream de funciones sin uso.
Guardar el trabajo antes de la primera sesión. Las pruebas reales requieren
una fase de instalación/activación separada de la preparación de fuentes.

## Fuentes y desarrollo

- `dwm/`, `dwmblocks/`, `dmenu/`, `st/`, `awesome/`: repositorios independientes,
  ignorados por el coordinador.
- `sources.tsv`: URL/revisión oficial de procedencia, importación local y árbol.
- `checkouts.tsv`: URLs personales y revisiones fijadas.
- [patches/README.md](patches/README.md): procedencia, dependencias y orden.
- `scripts/dependencies.tsv`: inventario exacto de comandos, módulos y unidades.

Cada checkout tiene una raíz propia con el código original y sus licencias,
seguida de commits locales por funcionalidad; no hereda historia oficial.
No hay submódulos. Para desarrollar en otro equipo, obtener primero los checkouts
fijados (las URLs GitHub admiten HTTPS) antes de `make test`, o usar el instalador
para obtener los ausentes. El instalador no ejecuta la validación completa.

Exportar una funcionalidad, con configuración y documentación separadas:

```sh
make patch PROJECT=dwm FEATURE=nombre
make test
```

Referencias: [paru](https://github.com/Morganamilo/paru),
[GTK](https://wiki.archlinux.org/title/GTK), [Qt](https://wiki.archlinux.org/title/Qt),
[Fusion](https://doc.qt.io/qt-6/qtquickcontrols-fusion.html),
[Git fetch](https://git-scm.com/docs/git-fetch) y
[systemctl](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html).
