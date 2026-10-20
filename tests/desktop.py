"""Synthetic desktop integration checks; never connect to a display/bus."""
import os
from pathlib import Path
import subprocess
import sys
import types

root, temporary = map(Path, sys.argv[1:])


def load(name):
    module = types.ModuleType(name)
    path = root / "scripts" / name
    exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    return module


launcher = load("wm-launcher")
notices = []
original_report = launcher.report
launcher.report = lambda name, message: notices.append((name, message))
assert "Fondo" not in launcher.actions()
assert launcher.actions()["Estado de energía"][0] == [
    "alacritty", "-e", "watch", "-n", "5", "upower", "--dump"]
assert (root / "session/dwm-xdg-terminals.list").read_text().splitlines() == [
    "Alacritty.desktop", "wm-st.desktop"]
assert "command\talacritty\talacritty\t/usr/bin/alacritty" in (
    root / "scripts/dependencies.tsv").read_text()
inventory = (root / "scripts/dependencies.tsv").read_text()
assert "command\tthunar\tthunar\t/usr/bin/thunar\n" in inventory
assert "command\tdolphin\t" not in inventory
repository = types.ModuleType("gi.repository")
repository.GLib = types.SimpleNamespace(Error=RuntimeError)
sys.modules["gi"] = types.ModuleType("gi")
sys.modules["gi.repository"] = repository
assert "\n" not in launcher.label("new\nline\udcff")

calls = []
original_run, original_popen = subprocess.run, subprocess.Popen
subprocess.Popen = lambda argv, **kw: calls.append((argv, kw))
subprocess.run = lambda argv, **kw: types.SimpleNamespace(returncode=0, stdout="arbitrary command\n")
assert launcher.choose({"legitimate": None}, "test") is None
subprocess.run = lambda argv, **kw: types.SimpleNamespace(returncode=1, stdout="legitimate\n")
assert launcher.choose({"legitimate": None}, "test") is None
menu_calls = []


def menu_run(argv, **kwargs):
    menu_calls.append(argv)
    assert "-c" in argv
    assert argv[argv.index("-m") + 1] == "2"
    return types.SimpleNamespace(returncode=0, stdout="legitimate\n")


subprocess.run = menu_run
assert launcher.choose({"legitimate": None}, "test", "2") == "legitimate"
assert menu_calls
subprocess.run = original_run


class App:
    def get_display_name(self):
        return "Duplicate\nname $(touch never)"

    def launch(self, files, context):
        assert files == [] and context is None
        calls.append("app")
        return True


# A stale index is ignored, and neither HOME nor the cache is accessed.
cache = temporary / "old-cache"
cache.mkdir()
index = cache / "files.json"
index.write_text('{"paths": ["old-file"]}')
os.environ["XDG_CACHE_HOME"] = str(cache.parent)
original_home, original_walk, original_open = Path.home, os.walk, Path.open


def no_files(*args, **kwargs):
    raise AssertionError("launcher accessed HOME, files or cache")


Path.home = no_files
os.walk = no_files
Path.open = no_files
launcher.apps = lambda: [App(), App()]
launcher.sys.argv = ["wm-launcher"]
actual_choose = launcher.choose


def select_app(rows, prompt, monitor=None):
    assert len(rows) == 2 + len(launcher.actions())
    assert len(rows) == len(set(rows))
    assert all("\n" not in row and "[Archivo]" not in row for row in rows)
    return next(row for row in rows if "[Aplicación]" in row)


launcher.choose = select_app
launcher.run()
assert calls == ["app"]
calls.clear()
launcher.choose = lambda rows, prompt, monitor=None: None
launcher.run()
assert not calls
launcher.choose = lambda rows, prompt, monitor=None: "Cancelar"
launcher.execute_action("Apagar")
assert not calls
def confirm(rows, prompt, monitor=None):
    assert monitor == "2"
    return "Confirmar"


launcher.choose = confirm
launcher.execute_action("Apagar", "2")
assert calls[0][0] == ["wm-run", "--", "systemctl", "poweroff"]
calls.clear()
launcher.execute_action("Pantallas", "2")
assert calls[0][0] == ["wm-run", "--", "wm-displays", "-m", "2"]
calls.clear()
os.environ.pop("XDG_SESSION_ID", None)
launcher.execute_action("Cerrar sesión")
assert not calls and notices[-1][0] == "Cerrar sesión"
launcher.choose = lambda rows, prompt, monitor=None: next(row for row in rows if "[Aplicación]" in row)


class BrokenApp(App):
    def launch(self, files, context):
        raise RuntimeError("synthetic GIO launch failure")


launcher.apps = lambda: [BrokenApp()]
launcher.run()
assert notices[-1][0] == BrokenApp().get_display_name()
assert "No se pudo iniciar" in notices[-1][1]
subprocess.run = lambda argv, **kwargs: calls.append(argv)
original_report("app", "synthetic message")
assert calls[-1] == ["wm-run", "--error", "app", "synthetic message"]
subprocess.run = original_run
Path.home, os.walk, Path.open = original_home, original_walk, original_open
assert index.read_text() == '{"paths": ["old-file"]}'
subprocess.Popen = original_popen
launcher.choose = actual_choose
print("PASS: apps/actions only, no HOME/index access, exact mapping, GIO launch and confirmations")
