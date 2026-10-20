# wm

Entorno X11 en desarrollo basado en dwm, dmenu y st. No está activado ni listo
para sustituir Plasma.

## Estado

Preparados la estructura y la primera serie de dwm: flotante, un tag, foco por
clic, mitades/cuartos, maximizar/restaurar, fullscreen, centrar, traslado entre
monitores y cierre normal. `tests/dwm-core.c` prueba funciones reales con Xlib
simulado; no abre un display.

st tiene una serie parcial: tamaño libre, transparencia, cursor parpadeante y
perfil de Alacritty, con tests Xlib/Xft simulados y UBSan. Falta scrollback/reflow.
También faltan la bandeja, los componentes de sesión y el lanzador combinado.
Windows+Espacio usa temporalmente dmenu_run. Configurar fuentes emoji no
acredita todavía su renderizado. Hay avisos de funciones upstream sin uso tras
retirar sus atajos, no una compilación libre de warnings.

## Organización

- `dwm/`, `dmenu/`, `st/`: repositorios propios independientes, ignorados aquí.
- `sources.tsv`: proyecto, URL oficial, revisión oficial de procedencia,
  commit raíz local de importación y árbol original (cinco campos TSV).
- `checkouts.tsv`: destinos personales y HEAD locales del checkpoint.
- `patches/`: diffs exportados y orden de aplicación por proyecto.
- `scripts/`: herramientas del proyecto; no hay instalador ni activación.
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
sin variables de sesión. La compilación no instala ni ejecuta los programas.

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
Pendiente: completar scrollback/reflow de st, después dmenu; bandeja y servicios
de sesión siguen pendientes. No activar aún.

## Seguridad de la sesión actual

No ejecutar `make install` dentro de los proyectos, ni arrancar sus binarios,
compositores o servicios desde esta fase de desarrollo. No modificar la sesión
actual de Plasma, el autostart, las credenciales ni la configuración de acceso.
Las pruebas visuales, de energía, autenticación y hardware quedan para una fase
posterior expresamente autorizada.
