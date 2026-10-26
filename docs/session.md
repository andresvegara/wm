# Sesión wm (X11)

Dwm gestiona ventanas, barra y bandeja; dwmblocks muestra indicadores. Rofi,
Dunst, Xfce Power Manager, xsettingsd y las herramientas de sesión resuelven el
resto. No se ejecuta el escritorio Xfce completo ni otro gestor de ventanas.
Bluebird es el tema predeterminado. Alacritty es la terminal; st y dmenu siguen
incluidos como alternativas, no como la interfaz principal.

Los cambios se preparan en fuentes: el instalador no inicia la sesión ni los
servicios. La validación automatizada no es una prueba visual, de autenticación
ni de suspensión real. Ver [instalación y dependencias](../README.md).

## Atajos

Super es la tecla Windows. Un tag y ventanas flotantes por defecto. El foco cambia
con el clic: mover el cursor no cambia la ventana ni el monitor activos; el clic
normal enfoca y eleva. Los docks no reciben foco. Jumpapp conserva las ventanas existentes
en su monitor; las normales nuevas aparecen centradas y los diálogos usan el
monitor del padre. Fullscreen/docks conservan sus reglas de colocación.

| Atajo | Acción |
| --- | --- |
| Super+Espacio | Rofi: aplicaciones, ventanas y acciones |
| Super+D | Comando libre con sugerencias de PATH, ejecutado en Alacritty |
| Alt+Tab / Alt+Shift+Tab | Selector nativo MRU global; soltar Alt activa, Escape cancela |
| Super+H / Super+T | Minimizar / alternar siempre encima |
| Super+F1 | Ayuda de atajos buscable en Rofi |
| Super+Escape / clic derecho en el fondo | Menú de acciones de sesión |
| Super+Intro | Abrir/enfocar/alternar Alacritty con Jumpapp |
| Super+W / Super+Shift+W | Brave / Chromium |
| Super+E | Thunar (`jumpapp -n -f thunar`) |
| Super+Shift+M / Super+Shift+C | Spotify / CopyQ |
| Super+flechas | Mitades; combinar ejes para cuartos; repetir libera el eje |
| Super+M / Super+F / Super+Ñ | Maximizar / fullscreen / centrar |
| Super+Shift+izquierda/derecha | Mover a otro monitor |
| Super+Q / Ctrl+Q / Alt+F4 | Solicitar cierre normal mediante WM_DELETE_WINDOW |
| Super+arrastrar con botón izquierdo/derecho | Mover/redimensionar |
| Super+Inicio / tecla reproducir | Pausar/reanudar |
| Super+Shift+RePág / Super+Shift+AvPág | Pista anterior/siguiente |
| Super+RePág / Super+AvPág / Super+Fin | Volumen +5% / -5% / silencio |
| Teclas multimedia y brillo | Controles habituales |
| Impr Pant / Super+L | Flameshot / bloquear esta sesión |

Alt+Tab conserva una lista fija por uso reciente durante cada ciclo, entre todos
los monitores e incluyendo minimizadas. Tab avanza, Shift+Tab retrocede y soltar
Alt o pulsar Intro activa y eleva la selección, sin cambiarla de monitor. Escape
cancela sin restaurar minimizadas; pasar el cursor no cambia el foco durante el
selector. El menú aparece en el monitor donde comenzó el ciclo. Los cambios de
geometría del escritorio cancelan el selector y los clientes cerrados se retiran.

Rofi sigue ofreciendo un selector de ventanas buscable desde Super+Espacio, que
también permite recuperar minimizadas. Selecciona por sí mismo el monitor del
cursor (`-monitor -5`): sus índices no se confunden con los de dwm/Xinerama.
La ayuda está también en Acciones y el menú de sesión: seleccionar una línea
solo cierra la ayuda, nunca ejecuta el texto como un comando.

El teclado inicial es ES/US (`es,us`, grupo ES); el indicador permite alternarlo.
Se configura antes de arrancar hijos y no se escribe en `/etc`.

## Inicio y barra de tareas

La barra inferior no muestra tags ni layout. «Inicio», a la izquierda, abre Rofi
con aplicaciones, ventanas y acciones, anclado abajo a la izquierda del monitor
del cursor. El resto del espacio muestra un botón por ventana de ese monitor,
sin agrupar por aplicación e incluyendo las minimizadas. Clic izquierdo activa y
restaura; clic en la ventana enfocada la minimiza. El orden no cambia al enfocar;
los títulos se reparten el espacio y se truncan. `[min]` identifica minimizadas y
las urgentes se resaltan. Indicadores, reloj y bandeja conservan su zona derecha.

## Barras de título y ventanas

Las titlebars de dwm están desactivadas por defecto (`showtitlebar = 0` en
`dwm/config.def.h`). Para recuperarlas, cambiar a `1` y reconstruir con un config.h
actualizado; si se mantiene un config.h propio, cambiar allí la opción. No afecta
a cabeceras dibujadas por las propias aplicaciones. Sin titlebar, Super+arrastrar
mueve/redimensiona; Super+M maximiza y Super+Q solicita cierre normal.

Con la opción activada, las ventanas que solicitan decoración usan una titlebar clásica, inspirada en
Bluebird Metacity: degradado azul, título centrado, colores activos/inactivos y
botones derechos de minimizar, maximizar/restaurar y cerrar. Es un dibujo propio,
no un motor Metacity ni una copia exacta de sus gráficos XPM. Los otros temas
recolorean las decoraciones desde su paleta. No se necesitan Cinnamon ni nuevas
bibliotecas de imagen.

- Clic normal enfoca y eleva; el clic continúa llegando a la aplicación.
  Pasar el cursor no enfoca ni eleva, tampoco cambia el monitor activo.
- Arrastrar el título mueve; doble clic maximiza/restaura. Super+arrastrar con
  botón derecho conserva la redimensión existente.
- Clic derecho sin modificadores en el título abre Siempre encima, Minimizar,
  Maximizar/restaurar y Cerrar. Super+clic derecho redimensiona, no abre el menú. Puede usarse con ratón o flechas/Intro; Escape cancela.
- Siempre encima no roba el foco y sigue por debajo del fullscreen seleccionado.
- Las minimizadas conservan geometría y se recuperan con su botón de la barra,
  Alt+Tab o Rofi.
- Docks y fullscreen no muestran titlebar. Al gestionar una ventana se respetan
  las indicaciones Motif sin título y `_GTK_FRAME_EXTENTS` de cabeceras propias;
  aplicaciones que no las comuniquen correctamente pueden requerir ajustes.
- Snap, maximización y centrado cuentan el espacio del título; fullscreen conserva
  una geometría de retorno separada. Cerrar sigue solicitando WM_DELETE_WINDOW,
  sin matar conexiones X ni saltarse confirmaciones de cambios sin guardar.

## Aplicaciones, comandos y acciones

Rofi utiliza sus modos `drun` y `window`; el modo propio «Acciones» añade Pantallas,
Apariencia, Ejecutar comando, Energía, Notificaciones, Red/VPN, contraseñas/SSH,
sonido, CopyQ, diagnóstico de energía y acciones de sesión. Las entradas de
aplicaciones y sus iconos pertenecen a Rofi, no a un catálogo duplicado de wm.

`wm-launcher` despacha acciones del catálogo y extensiones configuradas con argv.
Las etiquetas no se ejecutan como shell. Los menús propios usan índices y rechazan entrada libre;
suspender, reiniciar, apagar y cerrar sesión requieren confirmación, con Cancelar
primero. Cerrar sesión necesita `XDG_SESSION_ID`, sin adivinar otra sesión.

### Añadir aplicaciones y acciones al Inicio

Las aplicaciones se añaden mediante archivos `.desktop` en las rutas XDG
habituales, como `~/.local/share/applications/`; Rofi gestiona su descubrimiento.
Para acciones propias, crear `~/.config/wm/dwm/menu.json` (o bajo
`$XDG_CONFIG_HOME` si está definido), sin recompilar ni reinstalar:

```json
{
  "Mis documentos": {"argv": ["thunar", "/ruta/a/documentos"]},
  "Mi herramienta": {"argv": ["mi-herramienta", "--opcion"], "confirm": true}
}
```

Usar rutas absolutas para documentos: no se expanden `~`, variables ni shell.
`argv` es una lista no vacía de argumentos; `confirm` es booleano, por defecto
`false`. Etiquetas únicas, sin controles, espacios iniciales/finales ni guion
inicial. No se pueden sustituir acciones integradas. JSON o valores inválidos
producen error visible; no se ejecuta una selección desconocida. El límite del
archivo es 64 Ki caracteres. Esta extensión es exclusiva de dwm; Awesome conserva
su configuración nativa. Las acciones se ejecutan después de cerrar Rofi.

Super+D conserva un TTY y la salida hasta pulsar Enter. Solo en esa terminal se
interpreta el comando de shell escrito por el usuario; nunca se ejecuta como
código una etiqueta de ventana, aplicación, tema o notificación. Las sugerencias
usan dmenu_path; no se recorren documentos de HOME ni se mantienen índices de
archivos. Las cachés de aplicaciones que gestione Rofi no son índices de archivos.

Alacritty es también la preferencia XDG para las aplicaciones de terminal. No se
modifica su configuración personal. Jumpapp mantiene los atajos por aplicación;
Thunar puede abrir una ventana aunque su proceso esté ejecutándose sin ventanas.

Los atajos y acciones pasan por `wm-run`: notifica fallos de ejecución o errores
durante los primeros 1,5 segundos; usa xmessage como respaldo acotado si no puede
notificar. No garantiza detectar errores posteriores ni activaciones D-Bus que
retornen éxito antes de abrir una ventana.

## Barra, bandeja y avisos

La barra nativa está abajo en cada monitor, con tag, layout y título seleccionado;
no se convierte en una tasklist ni añade decoraciones por ventana. Reserva área
útil para ventanas flotantes y fullscreen puede cubrirla.

Estado y bandeja XEmbed permanecen en la primaria RandR, con primera pantalla como
respaldo. La bandeja no sigue el foco, no roba una selección X11 existente y no
trata los iconos como ventanas normales. snixembed sigue proporcionando el puente
SNI/AppIndicator, con sus limitaciones de compatibilidad.

Dwmblocks presenta teclado, perfil de energía, volumen, batería, avisos y reloj
local `%Y-%m-%d %H:%M:%S`. Cada comando está acotado por timeout; un bloque lento
puede retrasar la barra hasta ese límite, pero no se ejecuta dentro del proceso
de dwm. Los intervalos y señales están en `dwmblocks/config.h`.

- Teclado: clic alterna ES/US.
- Energía o batería: clic abre las preferencias de Xfce Power Manager.
- Volumen: clic silencio, rueda +/-5%, clic derecho pavucontrol. Máximo 100%.
- Avisos: clic abre historial y No molestar; muestra su estado y el número guardado.

No se arrancan cbatticon ni pasystray: los indicadores ya cubren esos accesos.
No se añade un servidor de audio. `wpctl` usa la salida existente y ajustar volumen
no desactiva el silencio. Brillo usa la clase backlight de brightnessctl y un
mínimo de hardware de 1; no controla DDC ni LEDs del teclado.

Dunst conserva hasta cien avisos y los OSD no entran en el historial. «Notificaciones»
permite recuperar un aviso, vaciar historial y activar No molestar con nivel50;
los críticos y OSD tienen una excepción superior. No existe otro motor de historial.
El clic izquierdo ejecuta la acción de la notificación y después la cierra. Abrir
la conversación concreta requiere que la aplicación publique esa acción; no se
adivina el chat a partir del texto ni se ejecuta su contenido como un comando.
Volumen y brillo sustituyen el OSD del mismo canal y muestran el estado real.

## Energía y bloqueo

La integración energética requiere **Xfce Power Manager 4.20 o posterior**.
Se arranca sin `--daemon`: en esa versión permanece en primer plano por defecto,
sin autostart XDG global ni escritorio Xfce. Si falta, su versión no es compatible
o falla su configuración, se deshabilita ese complemento sin cerrar dwm.
Sus preferencias son las normales de xfconf y se comparten con una posible sesión
Xfce del mismo usuario. La configuración se realiza al iniciar wm, no al instalar.

El supervisor configura la integración necesaria:
- `/general/LockCommand` de xfce4-session: `wm-lock`.
- Bloqueo al suspender: habilitado.
- Manejo de teclas de brillo y popup de Xfce: deshabilitados; los conserva dwm.
- Perfil AC `performance` y batería `balanced`: solo si no existe esa preferencia.

Las demás políticas existentes se conservan; tapa, inactividad, DPMS y alertas se
ajustan desde la interfaz del gestor. No se traduce ni importa power.json de Awesome.
Dwmblocks solo consulta estado: se retira el controlador `power-auto` independiente.
No habilitar un segundo gestor de energía ni volver a activar teclas duplicadas.

**xss-lock/i3lock es el único dueño del bloqueador.** El supervisor verifica el
inhibidor de sueño de xss-lock por PID y UID antes de iniciar Xfce Power Manager.
`wm-lock` solicita a logind bloquear `XDG_SESSION_ID`; no lanza otro i3lock.
xss-lock transfiere su inhibidor a `i3lock --nofork` para el bloqueo previo al
sueño. Se conserva el bloqueo inicial por inactividad de 600 segundos.

Si falta la sesión, no se obtiene el inhibidor, hay otro gestor o termina un hijo
crítico, el inicio/supervisión falla y limpia sus grupos propios. No se modifica
logind.conf. Los tests no acreditan que el driver, PAM y la pantalla real bloqueen
correctamente: esa comprobación corresponde al despliegue autorizado.

## Apariencia

Bluebird es el default de **dwm y Awesome**; se respetan elecciones ya guardadas.
El catálogo único de fuentes es `awesome/config/themes.json`, con `default`
explícito y lista ordenada `profiles`. El instalador lo entrega también como
`/usr/local/share/wm/themes.json` para los helpers externos.

«Apariencia» ofrece Actual, Menta y Bluebird. La paleta Bluebird sigue al tema
clásico de Shimmer Project: panel #212936 y selección #7e9ebd. Si faltan Bluebird
GTK o sus iconos elementary-xfce-dark, esos recursos usan Adwaita independientemente;
la paleta del WM sigue disponible. Menta exige sus recursos GTK/iconos.

xsettingsd controla GTK/iconos; archivos temporales privados proporcionan la paleta
Rofi y Dunst. La propiedad privada `_WM_THEME` actualiza los dos esquemas de dwm
y sus bordes sin reiniciar el WM. Dwm valida seis colores hexadecimales completos
antes de cambiar esquemas. El helper revierte consumidores/configuraciones ante
fallos de aplicación; si falla la persistencia, informa del error.

La elección dwm se guarda en `$XDG_CONFIG_HOME/wm/dwm/appearance`; Awesome conserva
su selección separada `wm/awesome/appearance`. No se fuerza GTK_THEME=Adwaita.
XSettings afecta a aplicaciones del mismo display X, no garantiza uniformidad
para Qt, libadwaita o aplicaciones con estilo propio. Qt mantiene Fusion.

Picom conserva GLX/vsync y la transparencia de las aplicaciones, pero no añade
sombras ni blur. No impone opacidades distintas según el foco: la señal de ventana
activa pertenece a los bordes/titlebars de dwm, no a un efecto del compositor.
El borde fino de 1 px puede resultar poco visible sin la decoración; no se ha
verificado la apariencia real ni diagnosticado el binario instalado por estos tests.

## Fondo de pantalla persistente

«Fondo de pantalla» está disponible desde Inicio, el modo Acciones y el menú de
sesión. Abre el selector de archivos de Zenity (GTK4 en Arch, sin GTK2). Al elegir
una imagen, feh la aplica en **fill** a cada pantalla: misma imagen por monitor,
sin deformar, recortando lo necesario. No es una imagen extendida entre monitores.
Cancelar no modifica la elección.

No se distribuye una imagen predeterminada. Sin imagen guardada ni default
instalado, se aplica el fondo liso #f6f5f4. Opcionalmente puede añadirse un
`wallpaper.png` local (ignorado por Git): el instalador lo copia sin modificar
a `/usr/local/share/wm/wallpaper.png`. Debe ser un archivo regular, no un enlace.
Si no se aporta, la instalación funciona igualmente y no borra un default
instalado anteriormente.

La utilidad copia cada nueva elección a
`$XDG_DATA_HOME/wm/dwm/wallpaper` (por defecto
`~/.local/share/wm/dwm/wallpaper`), en privado y sin cambiar su contenido. Por eso
se conserva aunque se mueva o borre el original. El archivo fijo no necesita
extensión. La copia guardada siempre prevalece sobre el default del paquete.

`wm-wallpaper --restore` la restaura al entrar en dwm y después de estabilizar
los cambios de monitores. No hay proceso de wallpaper permanente ni polling
adicional. La instalación no escribe preferencias de HOME ni sobrescribe la
imagen elegida. Awesome conserva su configuración de fondo independiente.

Se valida que la fuente sea un archivo regular no vacío; feh comprueba que puede
aplicarla. Primero se copia a un temporal del mismo directorio y solo después de
aplicarla correctamente se reemplaza atómicamente la copia guardada. Un fallo de
copia/aplicación/guardado conserva la elección anterior; si ya se intentó aplicar,
se intenta restaurar el fondo anterior y se notifica cualquier fallo de rollback.
Esto no garantiza recuperación ante un fallo físico del sistema o disco. Un fallo
de fondo no cierra la sesión. El directorio/copia/lock administrados deben ser
privados y no enlaces simbólicos; sí puede elegirse un enlace a una imagen fuente.

Los comandos usan argv, nunca shell, y `--no-fehbg` evita crear o modificar
`~/.fehbg`. No ejecutar scripts de fondos descargados. Waypaper no se integra:
para esta función no necesitamos backends Wayland, hooks shell ni slideshow.
Referencias: [feh](https://man.archlinux.org/man/feh.1) y
[Zenity](https://man.archlinux.org/man/zenity.1.en).

## Pantallas y geometrías

`wm-displays` conserva xrandr/autorandr, perfiles privados en
`$XDG_CONFIG_HOME/wm/displays`, posiciones relativas, duplicación y confirmación15s
con watchdog de reversión independiente. Los menús se muestran mediante Rofi.
Cancelar, cerrar el editor o agotar el plazo no confirma cambios. Un fallo al
guardar después de confirmar conserva la disposición y avisa de que no se guardó.

El watcher externo recibe eventos de `wm-randr-watch`, agrupados durante350ms.
No consulta xrandr en periodos estables; las lecturas usan `--current` para evitar
reprobes. Setup conocido: restauración; desconocido: notificación sin abrir un
asistente automáticamente. Foco y geometría no reaplican un perfil conocido.

La edición tiene lock por display, comprobación de topología y `xrandr --dryrun`.
No admite apagar todas las pantallas, ciclos de posiciones, escalado/reflexión ni
panning preexistentes. Rechaza nombres de modo incompatibles con autorandr. Una
salida físicamente desconectada no puede restaurarse; se intenta conservar una
conectada. Fallos de X/driver pueden impedir incluso esa recuperación.

Dwm conserva en memoria hasta16 disposiciones por ventana flotante abierta, sin
reabrir aplicaciones ni escribir títulos o geometrías de clientes en disco.
`_WM_DISPLAY_SETUP` coordina captura anterior al cambio y restauración estable;
se mantienen fullscreen/snap y la geometría normal de retorno. Docks/tiled quedan
excluidos. EDID idénticos o cambios de conector pueden hacer ambiguos los setups.
No activar simultáneamente otro servicio autorandr que aplique perfiles.

## Arranque, instalación y validación

El supervisor posee solo sus hijos/grupos. dwm y el bloqueador son críticos;
los fallos de notificaciones, bandeja, compositor, indicadores, applets, portapapeles,
agente de autorización, energía y observador de pantallas no cierran el escritorio,
ni siquiera si no pueden arrancar. Cada complemento dispone de hasta tres reinicios
por sesión, separados al menos cinco segundos. Agotados, permanece deshabilitado.
Si no puede limpiar su grupo, no lo duplica intentando reiniciarlo.

XSettings también es complementario, pero no se reinicia automáticamente: las
aplicaciones ya iniciadas conservan su PID para actualizar la apariencia. Su fallo
queda registrado y puede impedir cambios de tema hasta volver a entrar en sesión.
Reutiliza secretos/SSH existentes; si faltan, solicita sockets GNOME Keyring/GCR
sin habilitarlos persistentemente. Si falla esa solicitud, registra la pérdida de
funcionalidad sin cerrar dwm. No copia credenciales, altera PAM ni bloquea el llavero
al bloquear la pantalla.

Los errores fatales devuelven código de sesión 2, no el código 1 que SDDM reserva
para autenticación y que impide reiniciar la pantalla de acceso. No se abre un aviso
gráfico que retrase el cierre ni se mata Xorg como alternativa. Cerrar sesión sigue
requiriendo confirmación y un `XDG_SESSION_ID` explícito: `wm-supervisor --logout`
publica una petición privada para ese identificador y el supervisor sale normalmente
en el siguiente ciclo de supervisión (habitualmente un segundo, salvo que esté
esperando el arranque o recuperación de un componente).
No se usa `loginctl terminate-session`, que puede matar también al helper de SDDM.
Las peticiones antiguas o de otro identificador no cierran la nueva sesión.

### Avisos de funcionamiento degradado

La barra muestra `Fallos N` mientras hay complementos averiados, incluso si Dunst
no funciona (`Avisos ?`). El menú incluye **Estado de sesión**, también accesible
con `wm-supervisor --status`: muestra componentes afectados, recuperación o
agotamiento de reintentos sin ejecutar las filas seleccionadas. Si también falla
dwmblocks, este menú sigue disponible mediante Super+Escape.

Las incidencias nuevas se agrupan en un aviso cuando Dunst está disponible; si
Dunst estaba caído, el aviso se retrasa hasta su recuperación. Los reintentos del
mismo fallo no generan avisos repetidos. Si falla el propio envío del aviso, el
estado y el registro siguen disponibles. Un fallo recuperado se retira del contador.

El estado se conserva en `health.json`, privado y limitado, dentro del runtime
propio; no contiene títulos de ventanas ni contenido de notificaciones. Se valida
el identificador de sesión y se renueva al menos cada cinco segundos mientras la
supervisión avanza. Con más de quince segundos sin renovación, falta de archivo
o formato inválido se muestra estado no disponible (`Fallos ?`), nunca «sin fallos».
No sustituye comprobar bloqueo, suspensión y servicios reales.

El log queda en `$XDG_CACHE_HOME/wm/session-<pantalla>.log`; la sesión anterior se
conserva en el mismo nombre con sufijo `.previous`, ambos privados. El instalador rechaza
symlinks en destinos, prepara builds/copias en temporales y no activa la sesión
ni servicios. Actualizar fuentes, helpers y configuración conjuntamente y entrar
de nuevo en wm: un dwm antiguo no entiende la nueva propiedad de apariencia.

Validación: `make test`. Focalizada: `make test WM_TEST_SUITE=dwm-external` y
`make test WM_TEST_SUITE=dwm-package`. Incluyen comportamiento, sintaxis, builds,
ASan/UBSan, bindings reales, supervisor y empaquetado con procesos/buses/hardware
simulados. Los tests de almacenamiento nativo usan GIO contra archivos temporales.
No se inician programas gráficos, servidores X ni servicios reales.

Persisten límites que requieren comprobación real autorizada: rendering de temas,
emoji, Rofi con el servidor X, iconos, hotplug, bloqueo/PAM, suspensión y secretos.
Una suite verde no garantiza ausencia de errores de integración o de hardware.

## Fuentes

- [Rofi: modos](https://davatorium.github.io/rofi/current/rofi.1/)
- [Rofi: scripts y selección](https://davatorium.github.io/rofi/current/rofi-script.5/)
- [Dunst: acciones y clics](https://dunst-project.org/documentation/)
- [Dunst: historial, pausa y recarga](https://dunst-project.org/documentation/dunstctl/)
- [Xfce Power Manager](https://docs.xfce.org/xfce/xfce4-power-manager/preferences)
- [Arranque en primer plano y opciones reales de 4.20](https://github.com/xfce-mirror/xfce4-power-manager/blob/xfce-4.20/src/xfpm-main.c)
- [Xfce: ruta de bloqueo](https://github.com/xfce-mirror/libxfce4ui/blob/xfce-4.20/libxfce4ui/xfce-screensaver.c)
- [xss-lock](https://man.archlinux.org/man/xss-lock.1.en)
- [i3lock](https://github.com/i3/i3lock/blob/main/i3lock.1)
- [xsettingsd](https://man.archlinux.org/man/xsettingsd.1.en)
- [SDDM: códigos del helper](https://github.com/sddm/sddm/blob/v0.21.0/src/auth/Auth.h)
- [SDDM: retorno al acceso según código de salida](https://github.com/sddm/sddm/blob/v0.21.0/src/daemon/Display.cpp)
- [Bluebird](https://github.com/shimmerproject/Bluebird)
- [autorandr](https://github.com/phillipberndt/autorandr)
- [systray](https://dwm.suckless.org/patches/systray/)
- [snixembed](https://man.archlinux.org/man/snixembed.1.en)
