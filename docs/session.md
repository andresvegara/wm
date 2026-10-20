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
foco por clic, no por pasar el ratón.

| Atajo | Acción |
| --- | --- |
| Super+Espacio | Lanzador combinado |
| Super+Intro | Abrir/enfocar/alternar ventanas de st con jumpapp |
| Super+W / Super+Shift+W | Brave / Chromium con jumpapp |
| Super+E | Dolphin con jumpapp |
| Super+Shift+M | Spotify con jumpapp |
| Super+Shift+C | Mostrar CopyQ |
| Super+flechas | Mitades; combinar ejes para cuartos; repetir libera el eje |
| Super+M | Maximizar/restaurar, sin confundir con fullscreen |
| Super+F | Fullscreen/restaurar |
| Super+Ñ | Centrar |
| Super+Shift+izquierda/derecha | Mover a otro monitor |
| Alt+Tab / Alt+Shift+Tab | Ventana siguiente/anterior |
| Ctrl+Q / Alt+F4 | Pedir cierre normal; no matar aplicaciones sin WM_DELETE_WINDOW |
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

## Lanzador

Super+Espacio muestra aplicaciones, archivos por nombre y acciones, diferenciados
por etiquetas. GIO interpreta los archivos `.desktop`. Los nombres de archivos
no se ejecutan como shell; se buscan bajo HOME, excluyendo ocultos, dependencias,
cachés y enlaces simbólicos. El índice se renueva al invocar, con un intervalo
de 60 segundos; un archivo nuevo puede tardar en aparecer. No se busca contenido.

Acciones disponibles: pantallas (`lxqt-config-monitor`), fondo (`nitrogen`),
red/VPN (`nm-connection-editor`), contraseñas/SSH (`seahorse`), sonido
(`pavucontrol`), estado de energía (`st -e watch -n 5 upower --dump`), bloqueo,
suspensión, reinicio, apagado y cierre de sesión. Las cuatro últimas requieren
confirmación. Cancelar no ejecuta la acción. Cerrar sesión necesita
`XDG_SESSION_ID`; no se adivina otra sesión si falta.

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

El inventario acordado para la sesión incluye Dunst, Picom, Nitrogen, nm-applet,
agente Polkit LXQt, CopyQ, trayer y snixembed; GNOME Keyring/libsecret, GCR SSH
Agent y Seahorse; lxqt-config-monitor y herramientas de energía del sistema.
El inventario completo está en `scripts/dependencies.tsv`: incluye los comandos
del lanzador, libsecret y unidades de sistema/usuario necesarias. El instalador
comprueba esas unidades además de los ejecutables. No se ejecuta el autostart
XDG general de otros escritorios. Remmina y Flameshot quedan disponibles, sin
arranque automático; no se añaden servicios de audio ni cbatticon.

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

La integración acordada usa trayer para XEmbed y snixembed como puente SNI:
bandeja compacta abajo a la derecha del monitor primario RandR, sin barra completa.
Debe seguir cambios de primaria/geometría, nunca el foco. No es una bandeja
implementada dentro de dwm. snixembed tiene soporte AppIndicator limitado;
no se garantiza que todos los iconos de todas las aplicaciones sean compatibles.

«Pantallas» abre lxqt-config-monitor para posición, resolución, refresco,
rotación, activación y primaria. El supervisor restaura perfiles compatibles al
inicio y ante cambios de conexión física, sin bucles por sus propios cambios de
geometría. Consulta RandR cada dos segundos; los perfiles los guarda la GUI. No se promete escalado independiente por monitor ni validación de
hotplug real por los tests.

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
- [trayer: opciones y monitor primario](https://github.com/sargon/trayer-srg)
- [lxqt-config: configuración de pantallas](https://github.com/lxqt/lxqt-config)
- [xss-lock: bloqueo y suspensión](https://man.archlinux.org/man/xss-lock.1.en)
- [Dunst: configuración](https://dunst-project.org/documentation/)
- [Picom: configuración](https://github.com/yshui/picom)
- [GNOME Keyring](https://wiki.archlinux.org/title/GNOME/Keyring)
- [Unidades GCR en Arch](https://archlinux.org/packages/extra/x86_64/gcr-4/files/)
- [Unidades GNOME Keyring en Arch](https://archlinux.org/packages/extra/x86_64/gnome-keyring/files/)
- [NetworkManager](https://wiki.archlinux.org/title/NetworkManager)
- [systemctl: habilitación sin inicio](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [snixembed en Arch](https://archlinux.org/packages/extra/x86_64/snixembed/)
- [trayer en AUR](https://aur.archlinux.org/packages/trayer)
