# Shared session data and Rofi selection; no processes or configuration at import.
import ctypes
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time

DATA = Path(__file__).resolve().parent.parent / "share/wm"


def xsettings_owner():
    x11 = ctypes.CDLL("libX11.so.6")
    display_type = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = display_type
    x11.XDefaultScreen.argtypes = [display_type]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XInternAtom.argtypes = [display_type, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XGetSelectionOwner.argtypes = [display_type, ctypes.c_ulong]
    x11.XGetSelectionOwner.restype = ctypes.c_ulong
    x11.XCloseDisplay.argtypes = [display_type]
    connection = x11.XOpenDisplay(None)
    if not connection:
        raise RuntimeError("no se pudo consultar XSettings")
    try:
        atom = x11.XInternAtom(connection, ("_XSETTINGS_S" + str(x11.XDefaultScreen(connection))).encode(), 0)
        return x11.XGetSelectionOwner(connection, atom)
    finally:
        x11.XCloseDisplay(connection)


def command(argv, timeout=5):
    result = subprocess.run(argv, text=True, encoding="utf-8", capture_output=True,
                            timeout=timeout, check=True)
    return result.stdout.strip()


def rofi(*args):
    theme = os.environ.get("WM_ROFI_THEME", str(DATA / "rofi.rasi"))
    argv = ["rofi", "-no-config", "-theme", theme, "-monitor", "-5"]
    if os.environ.get("WM_DWM_RUNTIME"):
        icons = read_private(Path(os.environ["WM_DWM_RUNTIME"]) / "icon-theme")
        if icons:
            name = icons.strip()
            if not re.fullmatch(r"[A-Za-z0-9 _-]+", name):
                raise ValueError("tema de iconos inválido")
            argv += ["-icon-theme", name]
    return [*argv, *args]


def label(text):
    return "".join(c if c.isprintable() else " " for c in str(text))[:4096]


def choose(items, prompt):
    rows = list(items)
    if not rows:
        return None
    result = subprocess.run(rofi("-dmenu", "-i", "-no-custom", "-format", "i", "-p", prompt),
                            input="\n".join(label(row) for row in rows) + "\n",
                            text=True, encoding="utf-8", capture_output=True)
    if result.returncode:
        return None
    selected = result.stdout.strip()
    if not selected.isascii() or not selected.isdecimal():
        return None
    index = int(selected)
    return rows[index] if index < len(rows) else None


def themes(path=None):
    data = json.loads((path or DATA / "themes.json").read_text(encoding="utf-8"))
    profiles = {}
    for profile in data["profiles"]:
        name = profile["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z]{1,31}", name) or name in profiles:
            raise ValueError("identificador de tema inválido o duplicado")
        for key in ("gtk", "icons"):
            if not re.fullmatch(r"[A-Za-z0-9 _-]+", profile[key]):
                raise ValueError("recurso de tema inválido")
        policy = profile.get("resources")
        if policy not in (None, "required", "optional"):
            raise ValueError("política de recursos inválida")
        if policy == "optional" and not re.fullmatch(r"[A-Za-z0-9 _-]+", profile.get("fallback", "")):
            raise ValueError("fallback de tema inválido")
        for key in ("bg", "fg", "focus", "selected", "border", "minimized", "muted", "outline"):
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", profile[key]):
                raise ValueError("color de tema inválido")
        for key in ("panel_bg", "panel_fg", "panel_border"):
            if key in profile and not re.fullmatch(r"#[0-9a-fA-F]{6}", profile[key]):
                raise ValueError("color de panel inválido")
        profiles[name] = profile
    default = data["default"]
    if default not in profiles or profiles[default].get("resources") == "required":
        raise ValueError("tema predeterminado no disponible sin recursos externos")
    return profiles, default


def resources(profile):
    if not profile.get("resources"):
        return profile["gtk"], profile["icons"]
    home = Path.home()
    roots = [Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")), home / ".local/share"]
    roots += [Path(value) for value in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if value]
    present = []
    for kind, legacy, name, relative in (("themes", ".themes", profile["gtk"], "gtk-3.0/gtk.css"),
                                         ("icons", ".icons", profile["icons"], "index.theme")):
        paths = [home / legacy / name / relative, *[root / kind / name / relative for root in roots]]
        present.append(any(path.is_file() for path in paths))
    if profile["resources"] == "required" and not all(present):
        return None
    return tuple(profile[key] if found else profile["fallback"]
                 for key, found in zip(("gtk", "icons"), present))


def private_directory(path, create=True):
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("ruta privada inválida")
    for parent in (*reversed(path.parents), path):
        if parent.is_symlink():
            raise ValueError("enlace no permitido: " + str(parent))
        if not parent.exists():
            if not create:
                return False
            parent.mkdir(mode=0o700)
        if not parent.is_dir():
            raise ValueError("ruta no es directorio: " + str(parent))
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("directorio privado inseguro: " + str(path))
    return True


def read_private(path):
    if not private_directory(path.parent, create=False):
        return None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd) as source:
        info = os.fstat(source.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 4096):
            raise ValueError("archivo privado inseguro: " + str(path))
        return source.read(4097)


def open_private(path, truncate=False):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_nlink != 1):
            raise ValueError("archivo privado inseguro: " + str(path))
        if truncate:
            os.ftruncate(fd, 0)
        return os.fdopen(fd, "w+")
    except BaseException:
        os.close(fd)
        raise


def session_health():
    session = os.environ.get("XDG_SESSION_ID", "")
    runtime = os.environ.get("WM_DWM_RUNTIME", "")
    if not session or not runtime:
        raise RuntimeError("estado de sesión no disponible")
    directory = Path(runtime)
    if read_private(directory / "session.id") != session:
        raise RuntimeError("el estado no pertenece a esta sesión activa")
    content = read_private(directory / "health.json")
    if content is None:
        raise RuntimeError("estado de sesión todavía no disponible")
    data = json.loads(content)
    if (not isinstance(data, dict) or set(data) != {"session", "issues", "updated"}
            or data["session"] != session or not isinstance(data["issues"], dict)
            or len(data["issues"]) > 16 or type(data["updated"]) not in (int, float)
            or not math.isfinite(data["updated"])):
        raise ValueError("estado de sesión inválido")
    if not 0 <= time.monotonic() - data["updated"] <= 15:
        raise RuntimeError("estado de sesión desactualizado")
    for name, message in data["issues"].items():
        if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", name)
                or not isinstance(message, str) or not message or len(message) > 160
                or not message.isprintable()):
            raise ValueError("incidencia de sesión inválida")
    return data["issues"]


def write_private(path, content):
    private_directory(path.parent)
    read_private(path)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
