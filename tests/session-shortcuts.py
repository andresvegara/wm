"""Inspect compiled dwm bindings with inert callbacks; no X/audio/hardware access."""
import os
from pathlib import Path
import subprocess
import sys

root, temporary = map(Path, sys.argv[1:])
assert not any(os.environ.get(key) for key in
               ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS"))
work = temporary / "session-shortcuts"
work.mkdir()

# Keep the pre-session bindings explicit, including function arguments.
expected = {}


def binding(mod, key, function, *args):
    assert (mod, key) not in expected
    expected[mod, key] = (function, *map(str, args))


superkey, shift, alt, control = 64, 1, 8, 4
for mod, key, argv in (
    (superkey, "XK_space", ("wm-launcher", "-m", "")),
    (superkey, "XK_d", ("wm-command", "-m", "")),
    (superkey, "XK_F1", ("wm-launcher", "--shortcuts")),
    (superkey, "XK_Escape", ("wm-launcher", "--session-menu")),
    (superkey, "XK_Return", ("jumpapp", "-n", "st")),
    (superkey, "XK_w", ("jumpapp", "-n", "brave")),
    (superkey | shift, "XK_w", ("jumpapp", "-n", "chromium")),
    (superkey, "XK_e", ("jumpapp", "-n", "-f", "thunar")),
    (superkey | shift, "XK_m", ("jumpapp", "-n", "spotify")),
    (superkey | shift, "XK_c", ("copyq", "show")),
):
    binding(mod, key, "spawn", *argv)
for key, placement in (("Left", 1), ("Right", 2), ("Up", 4), ("Down", 8)):
    binding(superkey, "XK_" + key, "snapclient", placement)
for key, function in (("m", "togglemaximize"), ("f", "togglefullscreen"),
                      ("ntilde", "centerclient")):
    binding(superkey, "XK_" + key, function, 0)
for key, direction in (("Left", -1), ("Right", 1)):
    binding(superkey | shift, "XK_" + key, "tagmon", direction)
binding(alt, "XK_Tab", "alttab", 1)
binding(alt | shift, "XK_Tab", "alttab", -1)
binding(superkey, "XK_h", "minimize", 0)
binding(superkey, "XK_t", "toggleabove", 0)
binding(superkey, "XK_q", "killclient", 0)
binding(control, "XK_q", "killclient", 0)
binding(alt, "XK_F4", "killclient", 0)
assert len(expected) == 26

commands = {
    "play": ("playerctl", "play-pause"),
    "pause": ("playerctl", "pause"),
    "stop": ("playerctl", "stop"),
    "prev": ("playerctl", "previous"),
    "next": ("playerctl", "next"),
    "up": ("wm-control", "volume-up"),
    "down": ("wm-control", "volume-down"),
    "mute": ("wm-control", "mute"),
    "brightup": ("wm-control", "brightness-up"),
    "brightdown": ("wm-control", "brightness-down"),
    "capture": ("flameshot", "gui"),
    "lock": ("wm-launcher", "--action", "Bloquear"),
}
for key, command in (("Home", "play"), ("Prior", "up"), ("Next", "down"),
                     ("End", "mute"), ("l", "lock")):
    binding(superkey, "XK_" + key, "spawn", *commands[command])
for key, command in (("Prior", "prev"), ("Next", "next")):
    binding(superkey | shift, "XK_" + key, "spawn", *commands[command])
for key, command in (("AudioPlay", "play"), ("AudioPause", "pause"),
                     ("AudioStop", "stop"), ("AudioPrev", "prev"),
                     ("AudioNext", "next"), ("AudioRaiseVolume", "up"),
                     ("AudioLowerVolume", "down"), ("AudioMute", "mute"),
                     ("MonBrightnessUp", "brightup"), ("MonBrightnessDown", "brightdown")):
    binding(0, "XF86XK_" + key, "spawn", *commands[command])
binding(0, "XK_Print", "spawn", *commands["capture"])

functions = sorted({value[0] for value in expected.values()} | {"movemouse", "resizemouse"})
symbols = sorted({key for mod, key in expected})
source = r'''
#include <stdio.h>
#include <X11/Xlib.h>
#include <X11/keysym.h>
typedef union { int i; unsigned int ui; float f; const void *v; } Arg;
typedef struct {
    unsigned int mod; KeySym keysym; void (*func)(const Arg *); const Arg arg;
} Key;
typedef struct {
    unsigned int click, mask, button; void (*func)(const Arg *); const Arg arg;
} Button;
typedef struct { const char *symbol; void (*arrange)(void *); } Layout;
typedef struct {
    const char *class, *instance, *title; unsigned int tags; int isfloating, monitor;
} Rule;
enum { SchemeNorm, SchemeSel };
enum { PlaceLeft = 1, PlaceRight = 2, PlaceTop = 4, PlaceBottom = 8 };
enum { ClkClientWin, ClkRootWin, ClkStart };
static void tile(void *m) { (void)m; }
static void monocle(void *m) { (void)m; }
'''
# Callbacks deliberately cannot launch anything, even if the harness regresses.
source += "\n".join("static void %s(const Arg *a) { (void)a; }" % name
                    for name in functions)
source += '\n#include "config.def.h"\n'
source += 'int main(void) {\nsize_t i; const char *name, *symbol; const char *const *argv;\n'
source += 'for (i = 0; i < sizeof keys / sizeof *keys; i++) {\nname = "UNKNOWN"; symbol = "UNKNOWN";\n'
source += "\n".join('if (keys[i].func == %s) name = "%s";' % (name, name)
                    for name in functions) + "\n"
source += "\n".join('if (keys[i].keysym == %s) symbol = "%s";' % (key, key)
                    for key in symbols)
source += r'''
printf("%u\t%s\t%s", keys[i].mod, symbol, name);
if (keys[i].func == spawn) {
    argv = keys[i].arg.v;
    for (; *argv; argv++) printf("\t%s", *argv);
} else {
    printf("\t%d", keys[i].arg.i);
}
putchar('\n');
}
return 0;
}
'''
(work / "bindings.c").write_text(source)
subprocess.run(["cc", "-std=c99", "-pedantic", "-Wall", "-Wextra",
                "-Wno-unused-variable", "-Wno-unused-const-variable",
                "-I" + str(root / "dwm"), str(work / "bindings.c"),
                "-o", str(work / "bindings")], check=True)
result = subprocess.run([str(work / "bindings")], check=True, text=True, capture_output=True)
actual = {}
for line in result.stdout.splitlines():
    mod, symbol, *action = line.split("\t")
    key = (int(mod), symbol)
    assert key not in actual, ("binding collision", key)
    actual[key] = tuple(action)
assert actual == expected, {key: (expected.get(key), actual.get(key))
                            for key in expected.keys() | actual.keys()
                            if expected.get(key) != actual.get(key)}
assert len(actual) == 44
print("PASS: compiled session bindings, external menus, argv, collisions and existing shortcuts")
