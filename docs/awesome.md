# Sesión Awesome

Configuración propia para **Awesome 4.3 / Lua 5.3**, independiente de dwm y
Plasma. No es un fork del gestor. El instalador prepara ambas sesiones o solo
Awesome, sin activar servicios ni cambiar la sesión actual. st opaca es la terminal
predeterminada. La barra Aero opaca, Inicio con icono, tareas, lanzador, fondo,
encaje y supervisión se validan con tests aislados; no se ha iniciado GUI.
Las comprobaciones visuales y de hardware requieren una primera sesión real.

## Integración nativa

Awesome usa `naughty` para notificaciones y OSD, sin Dunst. Un propietario ajeno
del servicio de notificaciones provoca un error de inicio, nunca su terminación.
`notify-send` permanece como cliente. dwm conserva Dunst y su configuración.

Fondo persistente mediante el helper compartido wm-wallpaper: selector Zenity,
copia privada en $XDG_DATA_HOME/wm/awesome/wallpaper y feh fill por monitor,
sin rotación ni daemon. Restauración al entrar/cambiar pantallas; cancelar no cambia
la elección. No se comparte la preferencia dwm. Sin imagen se usa #f6f5f4. Menú nativo con **clic derecho sobre el
fondo** o **Super+Escape**: bloquear directamente; cerrar sesión, suspender,
reiniciar y apagar mediante Confirmar/Cancelar. Cerrar sesión llama awesome.quit,
no mata aplicaciones explícitamente; guardar el trabajo antes porque terminar
la sesión X puede cerrar clientes. Suspender conserva bloqueo previo.

Awesome no sustituye Polkit, red, secretos, bloqueo, audio o PPD.

## Instalación

El instalador único ofrece:

```sh
sh scripts/install.sh           # dwm + Awesome
sh scripts/install.sh --awesome # solo Awesome y compartidos
```

`make install` equivale a la primera opción. Ejecutar como usuario normal.
Ambas preparan el staging completo antes de la primera copia; ninguna activa
servicios ni cambia la sesión predeterminada.

La opción Awesome prepara todos sus archivos antes de copiar; rechaza destinos
simbólicos y ancestros enlazados. Repetirla no reescribe archivos idénticos con
permisos correctos. Usa sudo solo para las copias finales al sistema; con
`DESTDIR=/ruta/absoluta` copia al árbol indicado sin privilegios.
No inicia, habilita ni reinicia servicios ni selecciona escritorio. En Arch,
ambas opciones resuelven paquetes ausentes mediante `paru -S --needed` y vuelven
a comprobar el inventario antes de compilar. `--awesome` con DESTDIR comprueba
dependencias sin instalar paquetes del sistema; su ausencia aborta indicando
la ruta. Las entradas `awesome-*` de `scripts/dependencies.tsv` son su
inventario separado. `--awesome` no necesita Dunst, xsetroot, dwmblocks, dmenu
ni un checkout de dmenu; tampoco compila ni instala dwm. Compila el helper X11
`wm-close` y st en temporales desde fuentes versionadas; si falta el checkout st,
lo obtiene por HTTPS en un temporal y verifica la revisión fijada. Entrega st,
terminfo y `awesome-st.desktop`, seleccionada mediante xdg-terminal-exec.
El instalador de ambas variantes conserva dmenu y st para dwm.
No se borran binarios de una instalación anterior.

| Contenido | Destino |
| --- | --- |
| Configuración Lua propia, modo 644 | `/usr/local/share/wm/awesome/` |
| Wrapper y supervisor, modo 755 | `/usr/local/bin/awesome-session`, `/usr/local/bin/awesome-supervisor` |
| Helpers compartidos | `/usr/local/bin/wm-command`, `wm-launcher`, `wm-run`, `wm-control`, `wm-displays` |
| Cierre normal X11 | `/usr/local/bin/wm-close` |
| Preferencia de terminal st | `/usr/local/share/xdg-terminal-exec/awesome-xdg-terminals.list` |
| Selectores nativos | `awesome/config/picker.lua`, `launcher.lua`, `displays.lua` |
| Notificaciones nativas | `/usr/local/share/wm/awesome/widgets/notifications.lua` |
| Entrada de sesión, modo 644 | `/usr/local/share/xsessions/awesome.desktop` |

El supervisor selecciona explícitamente
`awesome -c /usr/local/share/wm/awesome/rc.lua`.
No se escribe ni se carga por defecto `~/.config/awesome/rc.lua`. Los helpers
son compartidos: actualizarlos afecta a futuras sesiones que los usen;
no borrar ni sustituir preferencias personales para resolver conflictos.

## Dependencias

La base Arch comprobada es el paquete `awesome`, con `lua53` y `lua53-lgi`.
Para tests se usa **lua5.3**, no el alias genérico `lua`.
Los módulos awful/wibox/gears pertenecen a Awesome, sin frameworks de temas.
El inventario incluye compilador/pkg-config y bibliotecas X11/Xft/fontconfig/FreeType
para st; el helper de cierre requiere libX11. ncurses/tic y
xdg-terminal-exec son requisitos propios de Awesome; Lua/lgi/GIO para los lanzadores nativos; Python
para el backend transaccional de pantallas; st y los proveedores de atajos;
nm-applet, CopyQ, Polkit, snixembed, bloqueo y secretos/GCR para la sesión.
Los widgets usan timeout de coreutils, setxkbmap y wpctl. Energía y batería
usan Lua/lgi/GIO con señales de UPower, PPD y logind; no tienen backend Python
ni daemon propio. UPower debe estar disponible; su ausencia deja fuente y
batería como desconocidas, sin imponer políticas basadas en datos inventados.
`xprintidle` solo se consulta si hay suspensión por inactividad configurada.
No se instala ni activa un servidor de audio ni PPD como efecto secundario:
si PPD/performance no está disponible, la barra lo indica sin iniciarlo.
Los sockets de secretos/SSH se comprueban como recursos; no se arrancan al instalar.

Referencias de herramientas:
[busctl en systemd](https://archlinux.org/packages/core/x86_64/systemd/files/),
[coreutils](https://archlinux.org/packages/core/x86_64/coreutils/).

Referencias oficiales:
- [Paquete Arch](https://archlinux.org/packages/extra/x86_64/awesome/).
- [API estable](https://awesomewm.org/doc/api/).
- [Selección explícita de configuración](https://awesomewm.org/doc/manpages/awesome.1.html).

## Validación reproducible

Validación focalizada de terminal y CopyQ, siempre aislada:

```sh
make test WM_TEST_SUITE=awesome-picker
make test WM_TEST_SUITE=awesome-terminal
make test WM_TEST_SUITE=awesome-copyq
make test WM_TEST_SUITE=awesome-package
```

El empaquetado verifica st y terminfo reales, ausencia de dmenu en --awesome y
conservación de ajustes personales de Alacritty. Los tests se han reanudado y
migrado a las interfaces nativas: no se recuperan los workers Python retirados.
La persistencia usa GIO real con archivos temporales sintéticos; procesos, buses,
procesos /proc y controles de hardware se simulan. No se ha iniciado GUI.

```sh
make test
```

Es la operación de validación completa del proyecto: reconstrucción y build de
fuentes legacy en temporales, comportamiento y pruebas Awesome integradas.
El prefijo de dwmblocks ya incluye un objetivo all y la reconstrucción conserva
config.h en proyectos sin plantilla config.def.h. La suite completa pasa sobre
fuentes sin artefactos generados ajenos, incluidos todos los prefijos y ambas
sesiones. No se inicia Awesome, X, un servicio ni GUI.

Para ejecutar **solo** el bloque Awesome (Lua, helpers, widgets, sesión,
comandos/TTY sintético y empaquetado):

```sh
make test WM_TEST_SUITE=awesome
```

No sustituye la regresión dwm/dwmblocks. Para ejecutar **solo** empaquetado:

```sh
make test WM_TEST_SUITE=awesome-package
```

El empaquetado prueba payloads sintéticos y entregados, builds reales temporales,
modos, idempotencia, coexistencia, fallos, dependencias, copias privilegiadas
simuladas y symlinks. También comprueba sintaxis del instalador, pero NO certifica
el comportamiento Lua, el supervisor, los comandos ni la suite completa. No usar
`awesome -k` como sustituto de pruebas de comportamiento.

## Elegir sesión y volver atrás

Después de autorizar instalación y pruebas manuales, comprobar que SDDM ofrece
la entrada Awesome junto a dwm y Plasma. Elegirla explícitamente para ese inicio;
no cambiar la sesión predeterminada durante la preparación. Para volver, cerrar
normalmente esa sesión y elegir dwm o Plasma en el gestor de acceso. No terminar
clientes ni agentes de otra sesión para facilitar la prueba.

## Uso preparado

Un tag flotante por pantalla, ventanas nuevas centradas en el monitor del ratón
salvo excepciones (fullscreen/docks); diálogos en el monitor de su padre.
Foco por clic; mover el cursor no cambia el foco. Barra de título clásica en
ventanas normales y diálogos: altura de 22 píxeles, fuente propia de 9 puntos,
icono y botones compactos para Minimizar, Maximizar/restaurar y Cerrar. Se puede arrastrar desde el título o el
icono; clic derecho y arrastre redimensiona. Maximizar comparte el estado de
Super+M; cerrar solicita el mismo cierre normal que los atajos. La decoración usa
los colores Actual/Menta y Awesome la oculta en fullscreen.
Barra inferior en cada monitor; estado y una bandeja en primaria/fallback,
no siguiendo foco; fullscreen por encima.

| Atajo | Acción |
| --- | --- |
| Super+Intro | Abrir/enfocar/alternar st opaca de forma nativa |
| Super+Espacio | Selector nativo de aplicaciones, Apariencia, Pantallas y acciones |
| Super+D | Prompt nativo; ejecuta en st con TTY y conserva salida hasta Enter |
| Super+flechas | Izquierda/derecha: mitades a toda altura; arriba/abajo: mitades a todo ancho; combinar: cuartos; repetir libera el eje |
| Super+M / Super+F | Maximizar/restaurar / fullscreen |
| Super+Ñ | Centrar |
| Super+Shift+izquierda/derecha | Trasladar a otro monitor |
| Alt+Tab / Alt+Shift+Tab | Selector de ventanas por uso reciente, avance/retroceso |
| Super+Q / Ctrl+Q / Alt+F4 | Solicitar cierre normal, nunca matar conexión X |
| Super+W / Super+Shift+W | Brave / Chromium |
| Super+E / Super+Shift+M / Super+Shift+C | Thunar / Spotify / CopyQ |
| Super+L / ImprPant | Bloqueo / Flameshot |
| Super+Escape / clic derecho en fondo | Menú de sesión nativo |

Super+Espacio abre un selector Lua/wibox en el monitor del cursor, con búsqueda
por nombre, descripción y palabras clave de las aplicaciones instaladas. Incluye
entradas explícitas **Apariencia**, **Pantallas**, **Ejecutar comando**, red,
sonido, contraseñas, CopyQ, energía y acciones de sesión. Las etiquetas se muestran
como texto; abrir una aplicación conserva las reglas de su archivo `.desktop`.
Las entradas `Terminal=true` usan st.

Escribir filtra la lista; arriba/abajo o Tab/Shift+Tab recorren opciones, Intro
elige y Escape cancela. También se puede pulsar una fila. Super+D permite
escribir un comando libre, con sugerencias de ejecutables de PATH y completado
mediante Tab. **Ctrl+V** pega el portapapeles normal mediante CopyQ de la sesión,
en el cursor y sin ejecutar nada. Saltos de línea y caracteres de control se
convierten en espacios. El texto total se limita a 4096 bytes, recortando solo
lo pegado en una frontera UTF-8 y conservando el texto previo. **Shift+Insert**
mantiene el pegado nativo de PRIMARY (selección del ratón). Intro ejecuta el texto literal si no se ha navegado por las
sugerencias; tras navegar, ejecuta la sugerencia resaltada. Los argumentos y
operadores de shell solo se interpretan dentro de la terminal solicitada.
La salida permanece visible hasta pulsar Enter. No se usa dmenu ni dmenu_path.

Los accesos compatibles `wm-launcher`, `wm-command` y `wm-displays` en una sesión
Awesome redirigen a estas funciones nativas. Los atajos llaman directamente a
Lua; no necesitan awesome-client ni traducir índices Xinerama. En dwm, los mismos
scripts conservan su interfaz anterior. Una instalación anterior seguirá usando
las rutas antiguas hasta actualizar los archivos y entrar de nuevo en Awesome.

El selector Alt+Tab incluye las ventanas normales y diálogos de todos los
monitores, también minimizadas. Mantén Alt para recorrer la lista; suéltalo
(o pulsa Intro) para confirmar, Escape para cancelar. La preselección no cambia
el foco ni restaura minimizadas; el orden permanece fijo durante cada ciclo.
La lista se desplaza para mantener visible la selección y se cancela si se
desconecta el monitor donde aparece.

Los atajos de st, Brave, Chromium, Thunar y Spotify usan el motor Lua
`config/apps.lua`; los comandos y políticas están separados en
`config/applications.lua`. Al entrar desde otra aplicación eligen la ventana
coincidente superior; dentro de la aplicación recorren el orden de gestión de
Awesome. Restauran minimizadas; por defecto no trasladan ventanas ni el cursor.
Sin ventana coincidente, buscan el proceso local por su argv[0]: si sigue abierto
sin ventana, informan y no duplican el arranque, salvo `force` (activo para Thunar).
Una espera máxima de ocho segundos contiene repeticiones durante el arranque.
No se ejecutan Jumpapp, wmctrl ni xdotool para estas acciones; dwm conserva su
integración anterior. st es la terminal predeterminada; Alacritty conserva su
perfil optativo y sus ajustes personales intactos.

st se usa desde Super+Intro, Super+D, Estado de energía y las entradas
`Terminal=true`. Los comandos conservan TTY y salida hasta Enter. La preferencia
`awesome-xdg-terminals.list` selecciona `awesome-st.desktop` solo para Awesome,
sin escribir preferencias personales ni cambiar dwm/Plasma. `--awesome` construye
st y terminfo en temporales, sin tocar artefactos del checkout.

### Opciones nativas de aplicaciones

Desde Lua: `apps.raise(nombre, argumentos, opciones)` o `apps.list(nombre, opciones)`.
`nombre` identifica un perfil; los argumentos son una lista de cadenas, sin shell.

| Capacidad de Jumpapp | Opción Lua |
| --- | --- |
| Ciclo inverso / forzar lanzamiento | `reverse` / `force` |
| Minimizar una única ventana enfocada | `minimize` |
| No lanzar sin ventana | `no_launch` |
| Pasar argumentos lanzando otra instancia | `passthrough` |
| Listar clientes coincidentes | `list()` |
| Clase / proceso alternativo | `class` / `process_name` |
| Filtrar título | `title_regex` o `title` exacto |
| Solo espacio actual / traer aquí | `current_workspace` / `bring_here` |
| Centrar cursor | `center_cursor` |
| Observar terminación sin bloquear | `on_exit(reason, code)` |

Las capacidades se adaptan al WM, sin copiar una interfaz CLI. Los títulos usan
expresiones **GLib**, no el dialecto Bash ERE; `process_name` compara exactamente
el basename de argv[0], sin la búsqueda por prefijo/regex del original. `on_exit`
es siempre asíncrono: nunca reemplaza ni bloquea Awesome como haría un `exec`.
El listado devuelve objetos cliente y los espacios son tags de Awesome.
Referencia de comportamiento: [Jumpapp original](https://github.com/mkropat/jumpapp).

### Apariencia

En el menú nativo, **Apariencia** permite elegir **Actual** (Adwaita y selección
azul), **Menta (MATE)** o **Bluebird (clásico)**. Menta usa el tema GTK `Menta`, iconos `menta` y una
paleta Awesome derivada del tema oficial; no es Mint-Y. La selección GTK usa
`#accd8a`; las barras de título Menta conservan fondo gris y texto oscuro,
separados de ese verde. Es una adaptación plana de la decoración de MATE,
sin reproducir sus degradados. Cambia barras, lista de
ventanas, bordes, selector y notificaciones. No modifica el fondo elegido.
La elección se guarda como un identificador en
`$XDG_CONFIG_HOME/wm/awesome/appearance` (por defecto `~/.config/wm/awesome/appearance`).

**Bluebird es el tema predeterminado** cuando no existe una elección guardada,
tanto en Awesome como en dwm; las elecciones existentes no se sobrescriben.
El catálogo compartido usa un campo default explícito.

Bluebird toma sus colores del [Bluebird de Shimmer Project](https://github.com/shimmerproject/Bluebird),
el tema incluido en [Debian para Cinnamon y otros escritorios GTK](https://packages.debian.org/bookworm/bluebird-gtk-theme):
gris `#dcdcdc`, selección azul `#7e9ebd`, títulos azules `#4e7aa9` con texto
claro y barra inferior oscura `#212936`. Los valores proceden de
[`_colors.scss`](https://github.com/shimmerproject/Bluebird/blob/master/gtk-3.0/_colors.scss)
y de las [constantes Metacity](https://github.com/shimmerproject/Bluebird/blob/master/metacity-1/metacity-theme-3.xml).
La adaptación Awesome conserva la altura compacta de 22 px y representa los
colores de forma plana, sin reproducir todos los relieves o degradados originales.
No inicia Cinnamon ni cambia sus preferencias.

La opción Bluebird siempre está disponible para Awesome. Si se encuentra el
tema GTK `Bluebird`, lo aplica también a las aplicaciones GTK; si falta, usa
Adwaita para esas aplicaciones y lo indica en el menú. Los iconos opcionales
`elementary-xfce-dark` siguen el mismo criterio, con Adwaita de respaldo.
Busca recursos en `~/.themes`, `~/.icons` y los directorios XDG; no los descarga
ni instala automáticamente. La elección Bluebird persiste y se restaura al
arrancar, incluso sin esos recursos opcionales.

El supervisor posee un `xsettingsd` privado y su configuración temporal, sin
reemplazar gestores existentes. Solo cambia tema GTK e iconos; no escribe
preferencias globales GTK, gsettings/dconf ni ajustes Plasma/MATE. El instalador
incluye `xsettingsd`, `mate-themes` y `mate-icon-theme`; elegir Menta sigue siendo
voluntario. Si faltan sus recursos, se conserva el aspecto Actual.

XSettings pertenece a la pantalla X: otras sesiones en displays distintos
conservan su apariencia. Las aplicaciones ejecutadas en la misma pantalla X
reciben sus ajustes, aunque procedan de otro escritorio. Menta upstream cubre
GTK2/GTK3; GTK4, libadwaita, Qt, Electron y estilos propios no tienen uniformidad
garantizada. Qt conserva Fusion. No se inicia el escritorio MATE.
Fuentes: [metatema Menta](https://github.com/mate-desktop/mate-themes/blob/master/desktop-themes/Menta/index.theme.in),
[GTK Settings](https://docs.gtk.org/gtk3/class.Settings.html).

La barra inferior de 32 píxeles se inspira en Windows Aero con degradados sólidos,
brillos y bordes, sin transparencia ni desenfoque. Inicio lleva un icono propio;
las tareas muestran icono y título, una por ventana sin agrupar. Un clic
activa/restaura; pulsar la activa la minimiza. El foco se distingue solo por
color y borde, sin cambiar el texto; los títulos reales siguen actualizándose.
`!` y `[min]` indican urgencia y minimización. Las cabeceras conservan su altura
compacta y comparten fuente, paleta, degradado opaco y controles con bordes de la barra.
Iconos acotados y títulos con elipsis dejan sitio al estado y a la bandeja.
Teclado, energía, volumen, batería y reloj aparecen en bloques individuales con
fondo y borde propios; separadores distinguen ventanas, indicadores y la bandeja
rotulada «Applets». Los controles muestran ayuda al pasar el cursor. El tema
Actual conserva selección azul y borde de foco más contrastado; fuentes y
compositor mantienen sus dependencias existentes.

Se conservan teclas multimedia, volumen y brillo. Los selectores usan directamente
las pantallas de Awesome, sin `wm-monitor` ni traducciones de índices.

Teclado ES/US (ES inicial); clic alterna mediante el widget nativo. Volumen:
clic mute, rueda +/-5%, clic derecho pavucontrol; controles/OSD existentes.
Energía: performance en AC y balanced en batería al inicio/transiciones;
selección manual hasta próxima transición conocida. Fuente desconocida no fuerza
perfil, fallos/degradación/ausencia se muestran. Batería y reloj 24h visibles.
Sin nuevas alarmas, políticas de tapa ni suspensión.

**Pantallas** usa el mismo selector nativo para activar/desactivar salidas,
elegir resolución, frecuencia, rotación y principal, colocar respecto a otra
pantalla, alinear y duplicar con un modo común. No abre dmenu ni el gestor de
ajustes de otro escritorio. La interfaz se ejecuta en Awesome; el backend
`wm-displays --awesome native-edit` recibe selecciones por un canal privado y
reutiliza xrandr/autorandr para leer y aplicar la disposición.

Al aplicar aparece **Revertir / Conservar y guardar** con cuenta atrás de 15
segundos. Cancelar, agotar el tiempo, reemplazar el selector o cerrar Awesome
cancela la edición; un watchdog separado restaura los cambios sin confirmar.
Desconectar una pantalla invalida la operación y conserva una salida visible.
El escalado, reflexión y panning existentes siguen fuera del editor.

Los perfiles conservan su almacenamiento anterior en `~/.config/wm/displays`
(o bajo XDG_CONFIG_HOME); no se migran ni eliminan. Se restauran por eventos de
Awesome, sin watcher permanente. Una combinación desconocida ofrece Configurar
sin abrir el editor automáticamente. Las geometrías por ventana se conservan
temporalmente por disposición. El backend y los monitores reales están
pendientes de validación; no se han aplicado cambios de pantalla en esta fase.

## Paridad y barra Aero

Inicio y Super+Espacio también buscan ventanas normales y diálogos de todos los
monitores, incluidas minimizadas. Elegir una restaura/enfoca/eleva sin trasladarla
ni mover el cursor. Las ventanas cerradas mientras el selector está abierto se ignoran.

Acciones personales en `$XDG_CONFIG_HOME/wm/awesome/menu.json` (o
`~/.config/wm/awesome/menu.json`), independientes de dwm:

```json
{"Mis documentos": {"argv": ["thunar", "/ruta/absoluta"], "confirm": false}}
```

Archivo regular de hasta 64 KiB; argumentos literales, sin shell ni expansión de
variables o `~`. No sustituye acciones integradas. `confirm: true` muestra
Cancelar/Confirmar. Se relee al abrir Inicio; errores invalidan el archivo entero
y se notifican sin ejecutar acciones personales.

Arrastrar desde el título de Awesome o con Super muestra un contorno opaco:
mitades en los lados, cuartos en esquinas y maximización en el borde superior.
Respeta tamaños mínimos/máximos, incrementos y proporciones; un destino imposible
no se ofrece. Al mover una ajustada recupera el tamaño normal bajo el cursor;
un clic sin movimiento no restaura. Escape revierte; cierre de cliente o cambios
de pantalla limpian preview y grabs. Redimensionar parte del rectángulo actual.

**Límite:** Awesome 4.3 no procesa `_NET_WM_MOVERESIZE`; el arrastre/redimensión
desde cabeceras dibujadas por aplicaciones no alcanza la paridad con dwm.
No se ha añadido un fork ni otro helper para resolverlo. Se conservan la
maximización EWMH y las acciones nativas de Naughty; la aplicación debe emitir
su solicitud de activación. No se adivina una ventana por el texto del aviso.
Fuentes: [event.c 4.3](https://github.com/awesomeWM/awesome/blob/v4.3/event.c),
[EWMH](https://github.com/awesomeWM/awesome/blob/v4.3/lib/awful/ewmh.lua) y
[Naughty D-Bus](https://github.com/awesomeWM/awesome/blob/v4.3/lib/naughty/dbus.lua).

Los complementos Picom, red, CopyQ, Polkit y puente de bandeja tienen hasta tres
reintentos con cinco segundos entre ellos; se confirma recuperación tras cinco
segundos estables. XSettings se deshabilita si falla, sin reiniciar un PID que
Lua conserva. Awesome y xss-lock siguen siendo críticos. «Estado de sesión» en
Inicio muestra incidencias actuales y contador de fallos desde un archivo privado
runtime, sin depender de Dunst/Naughty ni de su historial. Los avisos se agrupan.
No se termina ningún proceso ajeno para recuperar un complemento.

## Comprobaciones manuales pendientes

Solo después de autorización expresa, con salida disponible a dwm/Plasma:

- Entrada SDDM visible, rutas/argv correctos y configuración personal intacta.
- Inicio/fin limpios, sin procesos redundantes ni limpieza de agentes ajenos.
- Abrir aplicaciones y comandos; cancelar el lanzador no abre nada. Comando con
  éxito o error conserva la salida y espera Enter para cerrar.
- Notificaciones nativas: avisos normales y errores visibles;
  volumen/brillo actualizan un único OSD por canal sin acumular avisos. Cambiar
  mute también refleja estado real; no debe arrancar Dunst en Awesome ni terminar
  un notificador de otra sesión para apropiarse del bus.
- Fondo nativo: aplicación inicial y adaptación al cambiar
  geometría/primaria y conectar/desconectar pantalla, sin otro proceso de fondo.
- Menú con clic derecho/Super+Escape: cancelación sin efectos, errores visibles
  y confirmaciones acordadas. Comprobar bloqueo, suspensión/retorno y salida por
  separado: cerrar Awesome no debe apagar el equipo ni forzar cierre de clientes.
  Usar trabajo guardado y autorizar cada acción real antes de probarla.
- Atajos, clic para enfocar sin cambio al pasar el ratón, ventanas nuevas en
  el monitor del cursor y diálogos en el del padre; conservar posición al reiniciar.
- Alt+Tab MRU: avance/retroceso, soltar Alt/Intro, Escape, minimizadas, clientes
  cerrados durante selección y desconexión de pantalla con el selector abierto.
- Atajos de aplicación nativos: abrir, enfocar y recorrer varias ventanas,
  alias WM_CLASS reales, arranque lento y recuperación de minimizadas.
- Lista de ventanas por pantalla, iconos/títulos, contraste, muchas ventanas,
  clic de minimización/restauración, fullscreen y movimiento entre monitores.
- Snaps/restauración, centrado, fullscreen y cierre no forzado.
- Barra inferior, bandeja única en primaria/fallback y hotplug real.
- ES/US, volumen/OSD, batería y perfiles reales de energía, incluidos fallos.
- Bloqueo por inactividad y antes de suspender; autenticación real.
- Secretos, red y SSH sin prometer desbloqueo automático del llavero.
- Pantallas nativas: todos los ajustes, guardar, cancelar, cuenta atrás,
  reversión, perfiles y desconexión durante edición/confirmación.

La compatibilidad XEmbed no garantiza todos los iconos SNI. No se garantiza una
mejora de tirones: su causa sigue abierta. Los tests aislados no acreditan
renderizado, drivers, dock, PAM, audio o energía reales. Picom usa una configuración propia (`awesome-picom.conf`) con GLX y vsync,
sin sombras, desenfoque ni animaciones. Mantiene la composición en fullscreen.
Su eficacia contra tearing requiere comprobar el controlador y los monitores reales.
Si picom termina, Awesome sigue funcionando y el supervisor intenta recuperarlo
con el límite indicado; su salida queda en el log de sesión.
No modifica Plasma ni Alacritty personal.

«Fondo de pantalla», desde Inicio o el menú del escritorio, guarda una copia privada:
el original puede moverse o borrarse. Se aplica la misma imagen en fill a cada
monitor. La elección tiene almacenamiento propio y no cambia el fondo de dwm;
no se publica ninguna imagen personal.

## Energía y avisos

La energía está integrada en el ciclo de vida de Awesome. Se han retirado los
workers Python `config/power.py` y `widgets/backend.py` y su arranque independiente.
La barra, los ajustes y las acciones del menú de sesión comparten el controlador
Lua; suspender, reiniciar y apagar llaman a logind mediante D-Bus asíncrono,
conservando Confirmar/Cancelar y los inhibidores del sistema.

Super+Espacio → **Energía**, clic en batería o clic derecho en el perfil abre
opciones propias de Awesome. Permite elegir perfiles automáticos al conectar o
retirar corriente, desactivar ese cambio y configurar por separado en corriente
y batería: cierre de tapa, bloqueo, apagado de pantalla y suspensión por
inactividad. El perfil inmediato sigue disponible con clic izquierdo en PWR.
Hay una política independiente para la tapa con monitor externo activo, también
cuando se conecta a través de un dock.

Los ajustes se guardan privadamente en `$XDG_CONFIG_HOME/wm/awesome/power.json`.
Por defecto se conserva performance en corriente, balanced en batería, bloqueo
a los diez minutos y tapa delegada al sistema; no se añade suspensión automática
ni apagado de pantalla. Seleccionar Nunca desactiva esa función en Awesome.
Los ajustes de Plasma y `/etc/systemd/logind.conf` no se modifican.

Los monitores se obtienen de `screen.outputs` y las señales de Awesome: no hay
consulta periódica a XRandR. Fuente, baterías y perfiles se actualizan mediante
señales D-Bus y propiedades en caché de GIO, sin sondeos periódicos ni busctl.
Las lecturas de XRandR que necesita el editor transaccional usan `--current`
en Awesome, sin sondear cambios de hardware; dwm conserva su comportamiento.

El controlador solo toma control de la tapa con una acción explícita, la sesión
activa y ningún otro gestor controlándola. Libera su inhibidor al salir, perder
actividad o suspenderse. Las acciones siguen siendo delegar, ignorar, bloquear
o suspender. xss-lock conserva el bloqueo previo a suspensión. Se mantienen los
inhibidores block de sleep/idle y no se fuerza hibernación ni apagado por batería.

Awesome 4.3 no proporciona una API de inactividad/DPMS que sustituya estos
helpers: `xset` se ejecuta de forma asíncrona al cambiar la política o solicitar
bloqueo; `xprintidle` solo se lee cada dos segundos si la suspensión por
inactividad está activada y la sesión está activa. No se solapan consultas y
ambas herramientas tienen timeout. Con la configuración predeterminada no hay
ese temporizador de inactividad. El volumen conserva su lectura asíncrona de
wpctl cada cinco segundos; el reloj usa un temporizador Lua cada segundo.

Los ajustes conservan el mismo power.json, con lectura y escritura GIO asíncronas,
validación y sustitución atómica privada. No se crea el archivo al leer valores
predeterminados. Una configuración dañada se informa y no se sobrescribe.
Los permisos de logind/Polkit y el hardware necesitan validación real.

Los avisos de batería usan inicialmente 15% y 5%, configurables desde Energía.
Se emite como máximo un aviso por nivel y ciclo de descarga; conectar corriente
o recuperar cinco puntos sobre el umbral bajo los rearma. Con varias baterías
se usa el menor porcentaje conocido, sin fingir un porcentaje energético total.
El aviso crítico permanece hasta descartarlo o conectar el cargador.

Super+Espacio → **Notificaciones** ofrece las últimas cien notificaciones,
limpieza del historial y No molestar. El historial solo vive en memoria durante
esta instancia de Awesome; no guarda avisos en disco ni conserva acciones.
No molestar silencia avisos normales y los conserva en el historial; permite
críticos, OSD de volumen/brillo y consultas explícitas del historial.

Esta integración está preparada sin instalar ni activar nada. Las pruebas se
han reanudado: validan almacenamiento GIO en temporales, UI/eventos con dobles,
widgets y supervisión. No acreditan la corrección de todas las interacciones con
UPower/PPD/logind reales ni el comportamiento físico de tapa o suspensión.
Referencias: [logind e inhibidores](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html),
[UPower](https://upower.freedesktop.org/docs/UPower.html),
[GIO DBusProxy](https://docs.gtk.org/gio/class.DBusProxy.html).

## Iconos de la interfaz

El lanzador muestra el icono publicado por cada aplicación. Los selectores,
el menú de sesión y los indicadores de la barra añaden iconos del tema Actual
(Adwaita), Menta o Bluebird. Se consultan mediante Gtk.IconTheme, con imágenes acotadas
para mantener la alineación y sin sustituir las etiquetas por símbolos ambiguos.
Si falta GTK3 o un icono concreto se conserva el texto. Cambiar apariencia
actualiza los iconos de la barra y los selectores al abrirlos de nuevo.
La barra incorpora acceso directo al historial mediante **Avisos**.
No se ha realizado comprobación visual; los tests usan sustitutos de iconos y widgets.


## Diagnóstico del arranque

El supervisor guarda la salida de todos sus componentes en
`$XDG_CACHE_HOME/wm/awesome-session-<display-hash>.log` (por defecto
`~/.cache/wm/`). Conserva el intento anterior en el mismo nombre con sufijo
`.previous`, ambos privados. Cada arranque registra fecha UTC, PID, display y
ruta de configuración. Los fallos y su traceback quedan en este archivo,
además del resumen de SDDM en `~/.local/share/sddm/xorg-session.log`.

Las líneas `[awesome] begin` y `done` identifican la carga y configuración de
cada módulo con su duración: Apariencia, selectores, notificaciones, energía,
aplicaciones, pantallas, decoraciones, atajos y widgets. También se registran
GTK y el tema de iconos, búsquedas de iconos sin caché, fondo por monitor,
indicadores y barras por pantalla. Un `begin` sin su `done` permite localizar
una operación pendiente; `failed` incluye traceback. Los errores se escriben
antes de intentar mostrarlos como notificación. `ready event-loop` confirma
que terminó la configuración y Awesome empezó a despachar trabajo pendiente.

El supervisor reintenta comprobaciones que agotan su timeout individual,
con un plazo total de quince segundos por componente (una comprobación ya
iniciada puede añadir hasta tres segundos). La consulta Lua usa directamente
el método D-Bus de awesome-client con timeout de respuesta, evitando dejar
hijos del cliente shell al reintentar. Registra cada timeout,
la espera, confirmación y cierre de procesos. Un fallo de limpieza Lua no
impide detener los módulos restantes. Esta instrumentación queda preparada
sin ejecutar Awesome ni modificar una sesión activa; requiere actualizar la
instalación para que aparezca en un nuevo arranque.
