# wm

Sesión X11 independiente de Plasma basada en dwm, dmenu y st. Un escritorio,
ventanas flotantes, foco siguiendo el cursor, mitades/cuartos, maximización, barra nativa con bandeja,
lanzador combinado, notificaciones, compositor y bloqueo. Apariencia clara
Adwaita/Fusion solo en sus descendientes. No reemplaza ni desinstala Plasma.

La [guía de sesión](docs/session.md) recoge atajos, componentes y límites.
Barra de dwm siempre visible abajo, con bandeja XEmbed y puente snixembed;
sin tint2 ni otro panel. Reloj y bandeja en el monitor principal, barra en todos;
fullscreen puede cubrirla. Fondo liso claro, sin wallpaper ni selector;
no se requieren Nitrogen, Trayer ni GTK2 para esas funciones.
«Pantallas» abre un asistente dmenu con posiciones relativas y confirmación con
reversión en 15 segundos. Guarda automáticamente perfiles por combinación de
monitores y los restaura al iniciar/conectar/desconectar, mediante xrandr y
autorandr; no necesita el gestor de ajustes de otro escritorio.
La bandeja incluye batería (cbatticon) y volumen (pasystray); usa el audio existente,
sin añadir políticas de suspensión ni arrancar un servidor PulseAudio.

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
- Construye los tres programas y prepara todos los archivos en temporales antes
  de publicar. Rechaza enlaces en destinos y directorios padres.
- Usa sudo solo para copias finales y para habilitar SDDM/NetworkManager en
  próximos arranques. Detecta gestores competidores antes de copiar y no los
  deshabilita. Nunca inicia/reinicia servicios ni selecciona sesión.
- No escribe preferencias en HOME, no cambia Plasma, PAM ni políticas de tapa.
  No inicia ni habilita servicios de audio.
- Repetir actualiza solo archivos/permisos distintos. Un fallo durante copias o
  habilitación puede dejar una instalación parcial: corregir y repetir.
- `DESTDIR=/ruta/absoluta sh scripts/install.sh` empaqueta sin sudo ni habilitar
  servicios. **No es un sandbox:** comprueba dependencias/servicios del host y en
  Arch puede ejecutar paru. `WM_OS_RELEASE` y `WM_RESOURCE_ROOT` se reservan para
  las simulaciones de tests; no usarlos en instalaciones normales.

Después, guardar el trabajo, cerrar Plasma y elegir **wm** en SDDM. Si SDDM o
NetworkManager no estaban activos, reiniciar para usar los servicios habilitados.
Para volver, cerrar wm y elegir **Plasma**. No lanzar wm encima de KWin.

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

Para instalar **también la sesión manualmente**, después de los tres programas:

```sh
sudo install -Dm755 session/wm-session /usr/local/bin/wm-session
sudo install -Dm755 scripts/wm-supervisor /usr/local/bin/wm-supervisor
sudo install -Dm755 scripts/wm-launcher /usr/local/bin/wm-launcher
sudo install -Dm755 scripts/wm-run /usr/local/bin/wm-run
sudo install -Dm755 scripts/wm-control /usr/local/bin/wm-control
sudo install -Dm755 scripts/wm-displays /usr/local/bin/wm-displays
sudo install -Dm644 session/picom.conf /usr/local/share/wm/picom.conf
sudo install -Dm644 session/dunstrc /usr/local/share/wm/dunstrc
sudo install -Dm644 session/pulse-client.conf /usr/local/share/wm/pulse-client.conf
sudo install -Dm644 session/wm.desktop /usr/share/xsessions/wm.desktop
sudo install -Dm644 session/wm-st.desktop /usr/local/share/applications/wm-st.desktop
sudo install -Dm644 session/dwm-xdg-terminals.list /usr/local/share/xdg-terminal-exec/dwm-xdg-terminals.list
```

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
| Manuales | `/usr/local/share/man/man1` |
| Terminfo generado por el script | `/usr/local/share/terminfo` |
| Defaults de Dunst/Picom y cliente Pulse de pasystray | `/usr/local/share/wm` |
| Sesión X11 para SDDM | `/usr/share/xsessions/wm.desktop` |
| Entrada de st / selección de terminal | `/usr/local/share/applications`, `/usr/local/share/xdg-terminal-exec` |

`wm-session` aplica el entorno claro y terminfo a sus descendientes. No garantiza
el tema de GTK2, apps con temas propios, procesos ya abiertos, sandboxes ni apps
activadas por el bus fuera de ese árbol. st fuera de la sesión puede necesitar
`TERMINFO_DIRS=/usr/local/share/terminfo:` si se instaló con el script.

## Validación

```sh
make test
```

Reconstruye cada prefijo de parches y los tres programas en temporales. Prueba
funciones reales dwm/st con Xlib simulado y ASan/UBSan, historial/reflow, bindings,
lanzador, supervisor, agentes, monitores, bloqueo e instalador con comandos
simulados. Empaqueta dos veces fuentes reales y comprueba idempotencia/terminfo.
No instala ni arranca programas gráficos, X, servicios o hardware reales.

**No se ha validado una sesión gráfica real**, autenticación, monitores, emoji
compuesto, secretos/VPN o audio. Persisten avisos upstream de funciones sin uso.
Guardar el trabajo antes de la primera sesión; conservar Plasma como alternativa.

## Fuentes y desarrollo

- `dwm/`, `dmenu/`, `st/`: repositorios independientes del usuario, ignorados aquí.
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
