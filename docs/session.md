# Sesión wm (X11)

wm combina dwm, dmenu y st en una sesión independiente de Plasma. No reemplaza
ni desinstala Plasma, no importa sus preferencias y no necesita ejecutar KWin.
La apariencia Adwaita/Fusion se limita a los descendientes de la sesión wm.

El instalador incluye el supervisor, los defaults y el registro X11 en SDDM.
La validación es sintética, no una prueba visual ni de autenticación real.
Las instrucciones de instalación conjunta y por componente están en el
[README](../README.md). Conservar Plasma como alternativa para la primera prueba.

## Uso y atajos

Super es la tecla Windows. Se conserva un solo escritorio, ventanas flotantes y
foco siguiendo el cursor entre ventanas y monitores, también sobre el fondo
vacío. Los docks no reciben foco. Pasar el cursor no levanta ni mueve ventanas;
el clic sí las levanta. Los atajos abren ventanas nuevas/dmenu en el monitor
activo; jumpapp enfoca las existentes donde estén, sin trasladarlas.

| Atajo | Acción |
| --- | --- |
| Super+Espacio | Lanzador combinado |
| Super+Intro | Abrir/enfocar/alternar ventanas de Alacritty con jumpapp |
| Super+W / Super+Shift+W | Brave / Chromium con jumpapp |
| Super+E | Thunar con jumpapp (abre/enfoca/alterna ventanas) |
| Super+Shift+M | Spotify con jumpapp |
| Super+Shift+C | Mostrar CopyQ |
| Super+flechas | Mitades; combinar ejes para cuartos; repetir libera el eje |
| Super+M | Maximizar/restaurar, sin confundir con fullscreen |
| Super+F | Fullscreen/restaurar |
| Super+Ñ | Centrar |
| Super+Shift+izquierda/derecha | Mover a otro monitor |
| Alt+Tab / Alt+Shift+Tab | Ventana siguiente/anterior |
| Super+Q / Ctrl+Q / Alt+F4 | Pedir cierre normal; no matar aplicaciones sin WM_DELETE_WINDOW |
| Super+arrastrar con botón izquierdo/derecho | Mover/redimensionar |
| Super+Inicio / tecla reproducir | Pausar/reanudar |
| Tecla pausa / detener | Pausar / detener |
| Super+Shift+RePág / tecla pista anterior | Pista anterior |
| Super+Shift+AvPág / tecla pista siguiente | Pista siguiente |
| Super+RePág / tecla subir volumen | Subir volumen 5 %, máximo 100 % |
| Super+AvPág / tecla bajar volumen | Bajar volumen 5 % |
| Super+Fin / tecla silencio | Alternar silencio |
| Teclas de brillo | Subir/bajar retroiluminación 5 % |
| Impr Pant | Captura interactiva de Flameshot, sin guardado automático |
| Super+L | Acción «Bloquear» del lanzador |

Los extras de reproducción/volumen reproducen las combinaciones elegidas en
Plasma sin modificar su configuración. No se añaden atajos de micrófono,
retroceso/avance temporal ni pasos de volumen de 1 %.

`playerctl` usa su selección predeterminada de reproductor MPRIS: no se fuerza
Spotify ni se difunde la orden a todos los reproductores. `wpctl` controla la
salida predeterminada de WirePlumber/PipeWire; ajustar volumen no quita el silencio.
Estos bindings no arrancan ni habilitan servicios de audio. Si faltan servicios,
dispositivo o reproductor, la herramienta puede fallar sin efectuar la acción.

`brightnessctl` selecciona la clase `backlight`, no los LED del teclado; mantiene
un mínimo de hardware de 1 para no pedir apagar el panel. Necesita permisos del
sistema y un dispositivo compatible. No se configura DDC ni control individual
de brillo de monitores externos. No se usa sudo desde los atajos.

Las ventanas flotantes nuevas aparecen centradas en el área útil de su monitor.
Los diálogos transientes usan el monitor de su padre. No se recentran docks,
fullscreen ni ventanas existentes al redimensionarlas; las demasiado grandes se
alinean con la esquina superior izquierda sin cambiar su tamaño.

El supervisor aplica **teclado español de España (`es`, variante predeterminada)**
con `setxkbmap` antes de arrancar aplicaciones. No persiste ajustes en `/etc` ni
en las preferencias de Plasma. Si falla, no inicia los hijos de la sesión.

Los atajos de volumen/silencio/brillo usan `wm-control`. Tras aplicar el cambio,
consultan el nivel real y muestran un OSD Dunst de 1,5 s con barra porcentual;
pulsaciones sucesivas reemplazan el aviso del mismo tipo. Volumen y brillo se
serializan por separado para no mostrar estados viejos. El silencio se indica
sin desmutear al ajustar volumen. Se conservan pasos de 5%, tope 100% de volumen,
clase backlight y mínimo 1 de brillo. Si falla una acción o la lectura no es válida,
se muestra un error en vez de confirmar un nivel inventado. No se añaden servicios
ni captura de teclas por otro daemon; la bandeja pasystray conserva su configuración.

## Lanzador

Super+Espacio muestra solo aplicaciones y acciones del sistema, diferenciadas
por etiquetas, en un dmenu centrado horizontal y verticalmente en el monitor
activo. Las confirmaciones también se centran. El ancho se adapta al texto,
con un mínimo de 500 píxeles limitado al monitor. GIO interpreta los archivos
`.desktop`. No recorre HOME ni busca
archivos; no crea, lee ni actualiza índices. Los índices de versiones anteriores
se ignoran y no se borran automáticamente. Las etiquetas no se ejecutan como shell.

Acciones disponibles: pantallas (`wm-displays`), red/VPN (`nm-connection-editor`), contraseñas/SSH (`seahorse`), sonido
(`pavucontrol`), estado de energía (`alacritty -e watch -n 5 upower --dump`), bloqueo,
suspensión, reinicio, apagado y cierre de sesión. Las cuatro últimas requieren
confirmación. Cancelar no ejecuta la acción. Cerrar sesión necesita
`XDG_SESSION_ID`; no se adivina otra sesión si falta.

Alacritty es la terminal preferida de la sesión, también para aplicaciones
`.desktop` con `Terminal=true` mediante xdg-terminal-exec. st se conserva
instalado como alternativa; no se modifica la configuración personal de Alacritty.

Super+E usa `jumpapp -n -f thunar`: también puede abrir una ventana si Thunar ya
está en segundo plano sin ventanas normales. El instalador requiere `thunar`,
no Dolphin; no desinstala Dolphin ni cambia asociaciones de carpetas o ajustes
de Plasma. GVfs y sus backends son opcionales para papelera/montaje/red y no se
añaden automáticamente en este cambio.

Los comandos de atajos pasan por `wm-run`, que avisa mediante Dunst cuando no
puede ejecutar el programa o este termina con error durante los primeros 1,5 s.
Si falla la notificación intenta `xmessage` durante 15 s; los errores también
quedan en el registro de sesión. No se muestran argumentos ni stderr arbitrario
en el aviso. Jumpapp usa `-n` para observar el arranque sin cambiar foco/ciclo.
Las acciones del lanzador usan el mismo helper; los fallos GIO también se avisan.
No se promete detectar fallos posteriores, activaciones DBus asíncronas ni apps
que devuelven éxito sin abrir ventana. Las aplicaciones lentas no se cancelan.

## Dependencias y entrega al instalador

Además de las dependencias de compilación y aplicaciones ya descritas en el
README, los nuevos atajos necesitan:

| Ejecutable | Paquete Arch | Función |
| --- | --- | --- |
| `playerctl` | `playerctl` | Reproducción MPRIS |
| `wpctl` | `wireplumber` | Volumen y silencio; requiere una sesión de audio PipeWire/WirePlumber |
| `brightnessctl` | `brightnessctl` | Retroiluminación y permisos del sistema |
| `flameshot` | `flameshot` | Captura interactiva |
| `wm-launcher` | Entregado por wm | Bloqueo mediante la acción existente |

El bloqueo requiere además `xset`, `xss-lock` e `i3lock`, responsabilidad de la
integración de sesión. Los comandos de reproducción/volumen no justifican
sustituir un gestor de audio existente ni activar servicios nuevos sin acuerdo.

El inventario acordado para la sesión incluye Dunst, Picom, nm-applet,
agente Polkit LXQt, CopyQ, tint2, snixembed, cbatticon y pasystray; GNOME Keyring/libsecret, GCR SSH
Agent y Seahorse; autorandr/xrandr para pantallas y herramientas de energía del sistema.
El inventario completo está en `scripts/dependencies.tsv`: incluye los comandos
del lanzador, libsecret y unidades de sistema/usuario necesarias. El instalador
comprueba esas unidades además de los ejecutables. No se ejecuta el autostart
XDG general de otros escritorios. Remmina y Flameshot quedan disponibles, sin
arranque automático; no se añaden servicios de audio.

## Instalación futura y SDDM

Los destinos acordados son `/usr/local/bin/wm-session` y `wm-supervisor`, defaults
propios en `/usr/local/share/wm` y una entrada X11
`/usr/share/xsessions/wm.desktop` con `Exec=/usr/local/bin/wm-session`.
El instalador prepara todos ellos antes de publicar destinos. No copia
preferencias a HOME ni selecciona la sesión.

Una vez completada y autorizada la instalación, guardar el trabajo, cerrar la
sesión actual y elegir **wm** en SDDM. No lanzar dwm encima de Plasma/KWin ni usar
las instrucciones upstream de `.xinitrc` como procedimiento de migración.
La instalación no selecciona ni inicia la sesión. El contrato permite habilitar
SDDM/NetworkManager para futuros arranques solo sin gestores competidores;
no start/restart/disable. `DESTDIR` no habilita servicios.

Para volver, cerrar wm y elegir **Plasma** en el gestor de acceso. No se borran
preferencias de Plasma ni se cambia su configuración de apariencia. Si no se
puede completar el inicio de wm, volver a Plasma; no intentar arreglarlo
arrancando otro gestor de ventanas dentro de la sesión actual.

## Bandeja, pantallas y bloqueo

La integración usa tint2 para XEmbed y snixembed como puente SNI:
bandeja compacta abajo a la derecha del monitor primario RandR, con reloj y sin
barra completa ni tareas. El default `/usr/local/share/wm/tint2rc` usa anchura dinámica,
altura de 24 píxeles e iconos de hasta 20, sin reservar una franja de pantalla.
A la derecha de los iconos aparece la fecha y hora local en una línea:
`2026-10-20 03:04:05` (`%Y-%m-%d %H:%M:%S`), formato 24 horas con segundos y
ceros iniciales. Lo genera el reloj nativo de tint2, sin scripts adicionales.
El supervisor reinicia solo la bandeja ante cambios de primaria/geometría,
nunca por foco. No se necesitan Trayer ni Nitrogen; se mantiene un fondo liso
claro (#f6f5f4) con xsetroot, sin wallpaper ni acción «Fondo». No es una bandeja
implementada dentro de dwm. snixembed tiene soporte AppIndicator limitado;
no se garantiza que todos los iconos de todas las aplicaciones sean compatibles.

La bandeja incluye dos applets GTK3, arrancados después de tint2/snixembed:
- **Batería (`cbatticon`)**: estado, porcentaje/estimación en el tooltip y avisos
  propios (por defecto bajo 20%, crítico 5%). No se configuran comandos de clic,
  nivel bajo o crítico: no suspende ni cambia la política de energía/tapa.
- **Volumen (`pasystray`)**: rueda para volumen, clic central/Alt+clic para silencio
  y menú para elegir salida/entrada. Límite 100%, notificaciones desactivadas y
  sin capturar teclas multimedia (las conserva dwm). Usa el servidor Pulse
  compatible existente, por ejemplo pipewire-pulse. Solo este hijo recibe
  `PULSE_CLIENTCONFIG=/usr/local/share/wm/pulse-client.conf` con `autospawn = no`;
  no se lanza/instala un servidor de audio ni se tocan preferencias de HOME.
  Esto no deshabilita sockets o servicios ya configurados por el usuario.

El supervisor arranca una instancia de cada applet y limpia sus grupos al salir;
si terminan no cierra la sesión ni los relanza en bucle. Su visibilidad depende de
la batería, servidor de audio y tema de iconos disponibles. Son clientes de
bandeja, no módulos internos de tint2. Su presentación real queda por verificar.

«Pantallas» abre `wm-displays`, un asistente de menús dmenu centrados. Permite
activar/desactivar salidas, elegir resolución, frecuencia, rotación y principal,
y colocar cada pantalla a izquierda/derecha/arriba/abajo de otra, alineando sus
bordes o centros. Duplicar utiliza una resolución común; resolución y rotación
se cambian en la pantalla de referencia. Las posiciones relativas se recalculan
al editar el borrador; se guardan las posiciones resultantes. No se puede apagar
todo ni crear referencias circulares. Cancelar un menú vuelve atrás sin aplicar.

Pulsa **Aplicar y guardar** y confirma **Conservar y guardar** en 15 segundos.
Si cancelas, no confirmas, falla la aplicación o termina el configurador antes
de confirmar, un watchdog independiente restaura el estado anterior. Los límites
de modos/framebuffer se comprueban con `xrandr --dryrun`. Si guardar falla después
de confirmar, se conserva la disposición y se avisa de que no quedó persistida.
Una pantalla físicamente desenchufada no se puede restaurar: se conservan las
salidas presentes y, si no queda ninguna activa, se intenta activar una conectada.
Un fallo del servidor X o del driver puede impedir incluso esa recuperación.

El supervisor arranca `wm-displays --watch` después de dwm. Consulta cada dos
segundos y espera dos lecturas iguales de la combinación de salidas/EDID:
- **Setup conocido:** restaura el último perfil confirmado, sin preguntas.
- **Setup nuevo:** abre el asistente una vez; cancelar no vuelve a abrirlo en bucle.
  Puede retomarse desde «Pantallas». Al confirmar se guarda automáticamente.
- Los cambios de geometría, primaria o foco no reactivan perfiles. Un cambio de
  monitores durante un menú cierra el borrador y procesa el nuevo setup.

### Disposición de ventanas abiertas

Además del perfil de monitores, dwm recuerda posición, tamaño normal y monitor de
cada ventana flotante que siga abierta, para hasta **16 disposiciones** por ventana
(historial FIFO). Al volver a una disposición conocida se recuperan sus geometrías;
las ventanas nuevas no heredan posiciones de otras aplicaciones ni de XID reciclados.
Se mantiene el estado actual fullscreen/maximizado/mitades, recalculado en el monitor,
y se recupera también el rectángulo para volver a flotante. Docks y tiled se excluyen.
Se limita el rectángulo al área útil y se respetan las restricciones de tamaño de
la aplicación; una aplicación con mínimo mayor que el monitor puede sobresalir.

La clave de disposición incluye conexiones/EDID, salidas activas, modo, rotación,
posición y primaria. Si Xinerama reordena salidas idénticas sin cambios observables,
no se garantiza identificar el mismo monitor físico. El supervisor de pantallas
publica `_WM_DISPLAY_SETUP`: `pending` antes de aplicar y una clave al confirmar
estabilidad, bajo el lock de edición. dwm captura también antes del recolocado
por desconexión para no guardar el fallback sobre el setup anterior. Heartbeats
y cambios de foco no recentran ventanas ni roban foco a otra aplicación.

**No se guarda ningún título, clase de aplicación ni posición de ventana en disco.**
La memoria se olvida al cerrar la ventana o reiniciar dwm; no se reabren aplicaciones
ni se intenta adivinar qué ventana corresponde entre sesiones. Ambos componentes,
dwm y wm-displays, deben estar actualizados y en ejecución para coordinarlo.

Los perfiles de monitores de autorandr quedan solo en `$XDG_CONFIG_HOME/wm/displays/` (por defecto
`~/.config/wm/displays/`), con enlaces de publicación atómica a versiones privadas.
No editar esos enlaces ni habilitar un segundo servicio autorandr para wm. No se
leen/importan perfiles ni hooks personales/globales de autorandr o de Plasma.
La identidad incluye conector y EDID: cambiar de puerto puede definir otro setup;
sin EDID se usa el conector. Monitores con EDID idénticos pueden ser ambiguos.
Un lock por DISPLAY impide ediciones/restauraciones simultáneas. El watcher y sus
menús se cierran con la sesión; un watchdog pendiente termina tras revertir.

Las salidas desenchufadas que X11 aún mantiene configuradas se apagan antes de
crear snapshots. Si al conectar no queda ninguna pantalla activa, se intenta
activar una como recuperación, antes de mostrar el asistente.

No se necesita LXQt/KScreen para pantallas. No se cambian políticas de tapa ni
energía. El asistente rechaza transformaciones/escalado, reflexión y panning
preexistentes en lugar de borrarlos silenciosamente. Los nombres de modos con
espacios no son compatibles con el parser de autorandr y se rechazan antes de
aplicar cambios. No se ha validado hotplug
con hardware real.

«Bloquear» y Super+L usan exactamente `wm-launcher --action Bloquear`, que solicita
`xset s activate`: **sin xss-lock/i3lock activos esto no garantiza un bloqueo**.
El supervisor arranca xss-lock con i3lock y configura bloqueo tras 600 segundos
y antes de suspender. Si el proceso de bloqueo termina, la sesión se cierra
en lugar de continuar sin ese componente crítico.
No se añade suspensión por inactividad ni se cambia la política de tapa/logind
ni la energía de Plasma. No ejecutar suspensión real para probar los atajos.

GNOME Keyring y GCR no deben leer/migrar secretos ni sustituir agentes ajenos;
`SSH_AUTH_SOCK` se limita a la sesión wm. **Bloquear la pantalla no bloquea el
llavero.** SDDM/PAM con contraseña puede desbloquear el llavero de inicio si las
contraseñas coinciden; huella y autologin requieren un prompt para desbloquearlo.
No se edita PAM automáticamente ni se ponen contraseñas vacías. Si ya existe
un servicio de secretos o `SSH_AUTH_SOCK`, se reutiliza sin sustituirlo. Si no,
el supervisor activa los sockets de usuario GNOME Keyring/GCR; son servicios
compartidos y no los detiene al salir. No habilita esas unidades persistentemente.

El log de hijos está en `$XDG_CACHE_HOME/wm/session-<pantalla>.log` (por defecto
`~/.cache/wm/`); los errores de inicio se muestran también con xmessage. El
supervisor solo termina grupos de procesos que él arrancó. Si otra sesión ocupa
el gestor de ventanas, notificaciones o watcher de bandeja, aborta en vez de
reemplazarla.

El instalador rechaza un alias de gestor de acceso distinto de SDDM y gestores
conocidos de acceso/red activos o habilitados (incluidas instancias de dhcpcd y
netctl). Es una comprobación conservadora: no identifica administradores de red
personalizados con nombres arbitrarios. No deshabilitar un servicio para sortear
el aviso sin resolver antes quién administra las interfaces.

## Validación y límites

`make test` es la única operación de validación. El test de atajos compila la
tabla real con callbacks inertes y compara teclas, modificadores, funciones y
argv, incluidos los bindings anteriores y las colisiones. No ejecuta reproductores,
audio, capturas, bloqueo ni herramientas de hardware. Los tests del supervisor
simulan procesos, bus, reloj, agentes y RandR; los del instalador simulan Git,
paquetes, privilegios y systemctl, incluidas habilitación y detección de conflictos.
El gestor de pantallas se prueba con RandR/autorandr/dmenu simulados, geometrías y
EDID sintéticos, perfiles temporales, locks y watchdogs reales sobre pipes/fork,
sin conectar con X ni tocar monitores.

Los tests sintéticos no acreditan renderizado visual, emoji compuesto,
compositor, hardware, monitores/docks, autenticación PAM, bloqueo efectivo ni
persistencia real de secretos o VPN. Instalar, activar y probar esos elementos
requiere una fase posterior autorizada.

## Referencias de las herramientas

- [playerctl: comandos y selección del reproductor](https://github.com/altdesktop/playerctl)
- [wpctl: volumen, límite e identificadores predeterminados](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html)
- [brightnessctl: clase, mínimo y permisos](https://github.com/Hummer12007/brightnessctl)
- [Flameshot: interfaz de captura y opciones](https://flameshot.org/docs/advanced/commandline-options/)
- [snixembed: alcance y soporte AppIndicator](https://man.archlinux.org/man/snixembed.1.en)
- [tint2: bandeja, tamaño dinámico y monitor primario](https://man.archlinux.org/man/tint2.1.en)
- [cbatticon: batería y comandos opcionales](https://github.com/valr/cbatticon)
- [pasystray: controles y opciones](https://man.archlinux.org/man/pasystray.1.en)
- [PulseAudio: configuración de clientes y autospawn](https://wiki.freedesktop.org/www/Software/PulseAudio/FAQ/)
- [autorandr: perfiles y aplicación de configuraciones](https://github.com/phillipberndt/autorandr)
- [xrandr: modos, posición y rotación](https://www.x.org/releases/current/doc/man/man1/xrandr.1.xhtml)
- [xss-lock: bloqueo y suspensión](https://man.archlinux.org/man/xss-lock.1.en)
- [Dunst: configuración](https://dunst-project.org/documentation/)
- [Picom: configuración](https://github.com/yshui/picom)
- [GNOME Keyring](https://wiki.archlinux.org/title/GNOME/Keyring)
- [Unidades GCR en Arch](https://archlinux.org/packages/extra/x86_64/gcr-4/files/)
- [Unidades GNOME Keyring en Arch](https://archlinux.org/packages/extra/x86_64/gnome-keyring/files/)
- [NetworkManager](https://wiki.archlinux.org/title/NetworkManager)
- [systemctl: habilitación sin inicio](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [snixembed en Arch](https://archlinux.org/packages/extra/x86_64/snixembed/)
- [tint2 en Arch](https://archlinux.org/packages/extra/x86_64/tint2/)
