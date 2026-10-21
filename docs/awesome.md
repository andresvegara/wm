# Sesión Awesome (en preparación)

Configuración propia para **Awesome 4.3 / Lua 5.3**, independiente de dwm y
Plasma. No es un fork del gestor. La preparación no instala ni activa la sesión.
Los tests aislados de núcleo/widgets/sesión/comandos y empaquetado pasan.
El cierre conjunto del árbol de trabajo y las comprobaciones visuales/hardware
siguen pendientes. No usar esta guía como autorización
para instalar o cambiar la sesión actual.

## Instalación futura, solo con permiso

La opción nueva es explícita:

```sh
sh scripts/install.sh --awesome
```

Sin argumentos, el instalador conserva la selección dwm existente. `make install`
no cambia silenciosamente a Awesome. No ejecutar ninguno durante la preparación.

La opción Awesome prepara todos sus archivos antes de copiar; rechaza destinos
simbólicos y ancestros enlazados. Repetirla no reescribe archivos idénticos con
permisos correctos. Usa sudo solo para las copias finales al sistema; con
`DESTDIR=/ruta/absoluta` copia al árbol indicado sin privilegios.
No inicia, habilita ni reinicia servicios, no selecciona escritorio y no instala
paquetes automáticamente. Las dependencias finales de la sesión deben estar
resueltas antes del despliegue; las entradas `awesome-*` de
`scripts/dependencies.tsv` son su inventario separado. Una dependencia ausente
aborta indicando su ruta, sin ejecutar paru. No necesita dwmblocks ni picom y
no compila/instala dwm o st. Compila en temporal el dmenu parcheado local (para
`-c`, `dmenu_path` y `stest`) y los helpers X11 `wm-close`/`wm-monitor`.
Requiere ese checkout local; no lo descarga ni usa un dmenu genérico del sistema.

| Contenido | Destino |
| --- | --- |
| Configuración Lua propia, modo 644 | `/usr/local/share/wm/awesome/` |
| Wrapper y supervisor, modo 755 | `/usr/local/bin/awesome-session`, `/usr/local/bin/awesome-supervisor` |
| Helpers compartidos | `/usr/local/bin/wm-command`, `wm-launcher`, `wm-run`, `wm-control` |
| Helpers X11 | `/usr/local/bin/wm-close`, `/usr/local/bin/wm-monitor` |
| dmenu parcheado | `/usr/local/bin/dmenu`, `dmenu_path`, `dmenu_run`, `stest` |
| Notificaciones | `/usr/local/share/wm/dunstrc` |
| Entrada de sesión, modo 644 | `/usr/local/share/xsessions/awesome.desktop` |

El supervisor selecciona explícitamente
`awesome -c /usr/local/share/wm/awesome/rc.lua`.
No se escribe ni se carga por defecto `~/.config/awesome/rc.lua`. Los helpers y
Dunst son compartidos: actualizarlos afecta a futuras sesiones que los usen;
no borrar ni sustituir preferencias personales para resolver conflictos.

## Dependencias

La base Arch comprobada es el paquete `awesome`, con `lua53` y `lua53-lgi`.
Para tests se usa **lua5.3**, no el alias genérico `lua`.
Los módulos awful/wibox/gears pertenecen a Awesome, sin frameworks de temas.
El inventario incluye compilador/pkg-config y bibliotecas X11/Xft/Xinerama para
los builds; Python/GIO para el lanzador; Alacritty y los proveedores de atajos;
Dunst, nm-applet, CopyQ, Polkit, snixembed, bloqueo y secretos/GCR para la sesión.
Los widgets usan timeout de coreutils, busctl de systemd, setxkbmap y wpctl.
El backend Python de widgets también se instala, modo644, sin daemon adicional.
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

```sh
make test
```

Es la operación de validación completa del proyecto: reconstrucción y build de
fuentes legacy en temporales, comportamiento y pruebas Awesome integradas.
El árbol intermedio actual aún falla en el prefijo importado de dwmblocks:
no ofrece `make all`. Esto NO se omite ni se considera validado; dwmblocks sigue
pausado y no es requisito del instalador Awesome. El baseline legacy separado
sí pasó su suite completa. No se inicia Awesome, X, un servicio ni GUI.

Para ejecutar **solo** el bloque Awesome (Lua, helpers, widgets, sesión,
comandos/TTY sintético y empaquetado):

```sh
make test WM_TEST_SUITE=awesome
```

No certifica los borradores legacy. Para ejecutar **solo** empaquetado:

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

Un tag flotante por pantalla, ventanas nuevas centradas salvo excepciones
(fullscreen/docks), foco con el cursor. Barra inferior en cada monitor; estado
y una bandeja en primaria/fallback, no siguiendo foco; fullscreen por encima.

| Atajo | Acción |
| --- | --- |
| Super+Intro | Alacritty mediante jumpapp |
| Super+Espacio | Aplicaciones/acciones, sin indexar HOME |
| Super+D | Comando en Alacritty con TTY; éxito cierra, error espera Enter |
| Super+flechas | Mitades/cuartos, repetición restaura eje |
| Super+M / Super+F | Maximizar/restaurar / fullscreen |
| Super+Ñ | Centrar |
| Super+Shift+izquierda/derecha | Trasladar a otro monitor |
| Alt+Tab / Alt+Shift+Tab | Cambiar foco |
| Super+Q / Ctrl+Q / Alt+F4 | Solicitar cierre normal, nunca matar conexión X |
| Super+W / Super+Shift+W | Brave / Chromium |
| Super+E / Super+Shift+M / Super+Shift+C | Thunar / Spotify / CopyQ |
| Super+L / ImprPant | Bloqueo / Flameshot |

Se conservan teclas multimedia, volumen y brillo. `wm-monitor` resuelve el
rectángulo de Awesome al índice Xinerama de dmenu sin sondeo permanente.

Teclado ES/US (ES inicial); clic alterna mediante el widget nativo. Volumen:
clic mute, rueda +/-5%, clic derecho pavucontrol; controles/OSD existentes.
Energía: performance en AC y balanced en batería al inicio/transiciones;
selección manual hasta próxima transición conocida. Fuente desconocida no fuerza
perfil, fallos/degradación/ausencia se muestran. Batería y reloj 24h visibles.
Sin nuevas alarmas, políticas de tapa ni suspensión.

**Pantallas sigue bloqueado:** no hay watcher ni consumidor del protocolo privado
de dwm en Awesome. La acción compartida aún apunta al helper legacy wm-displays,
que este paquete no instala. No usarla como integración autónoma ni dar por
resueltos perfiles automáticos/restauración; requiere acuerdo e implementación.

## Comprobaciones manuales pendientes

Solo después de autorización expresa, con salida disponible a dwm/Plasma:

- Entrada SDDM visible, rutas/argv correctos y configuración personal intacta.
- Inicio/fin limpios, sin procesos redundantes ni limpieza de agentes ajenos.
- Atajos, foco, snaps/restauración, centrado, fullscreen y cierre no forzado.
- Barra inferior, bandeja única en primaria/fallback y hotplug real.
- ES/US, volumen/OSD, batería y perfiles reales de energía, incluidos fallos.
- Bloqueo por inactividad y antes de suspender; autenticación real.
- Secretos, red y SSH sin prometer desbloqueo automático del llavero.
- Pantallas/perfiles/restauración solo cuando su integración esté resuelta.

La compatibilidad XEmbed no garantiza todos los iconos SNI. No se garantiza una
mejora de tirones: su causa sigue abierta. Los tests aislados no acreditan
renderizado, drivers, dock, PAM, audio o energía reales. La primera versión se
prepara sin picom, blur ni animaciones; no modifica Plasma ni Alacritty personal.
