"""Synthetic desktop integration checks; never connect to a display/bus."""
import json
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
assert "Fondo" not in launcher.actions()
repository = types.ModuleType("gi.repository")
repository.GLib = types.SimpleNamespace(Error=RuntimeError)
sys.modules["gi"] = types.ModuleType("gi")
sys.modules["gi.repository"] = repository
home = temporary / "launcher-home"
cache = temporary / "launcher-cache"
home.mkdir()
for name in ("normal", "español 😀", "$(touch never);\nnew", "-option", ".hidden"):
    (home / name).write_text("synthetic")
for directory in (".cache", "node_modules", "vendor", "visible"):
    (home / directory).mkdir()
    (home / directory / "entry").write_text("synthetic")
(home / "link").symlink_to(home / "visible", target_is_directory=True)
paths = launcher.indexed_files(home, cache)
assert set(paths) == {"normal", "español 😀", "$(touch never);\nnew", "-option", "visible/entry"}
assert (cache / "files.json").stat().st_mode & 0o777 == 0o600
(home / "new-file").touch()
assert "new-file" not in launcher.indexed_files(home, cache)
data = json.loads((cache / "files.json").read_text())
data["time"] = 0
(cache / "files.json").write_text(json.dumps(data))
assert "new-file" in launcher.indexed_files(home, cache)
# Cache cannot smuggle absolute paths or traversals into the file menu.
data["time"] = launcher.time.time()
data["paths"] = ["../../not-home"]
(cache / "files.json").write_text(json.dumps(data))
assert "../../not-home" not in launcher.indexed_files(home, cache)
assert "\n" not in launcher.label("new\nline\udcff")

calls = []
original_run, original_popen = subprocess.run, subprocess.Popen
subprocess.Popen = lambda argv, **kw: calls.append((argv, kw))
subprocess.run = lambda argv, **kw: types.SimpleNamespace(returncode=0, stdout="arbitrary command\n")
assert launcher.choose({"legitimate": None}, "test") is None
subprocess.run = lambda argv, **kw: types.SimpleNamespace(returncode=1, stdout="legitimate\n")
assert launcher.choose({"legitimate": None}, "test") is None
subprocess.run = original_run


class App:
    def get_display_name(self):
        return "Duplicate\nname"

    def launch(self, files, context):
        assert files == [] and context is None
        calls.append("app")


original_home = Path.home
Path.home = lambda: home
os.environ["XDG_CACHE_HOME"] = str(cache.parent / "menu-cache")
launcher.apps = lambda: [App(), App()]
launcher.sys.argv = ["wm-launcher"]
actual_choose = launcher.choose


def select_file(rows, prompt, monitor=None):
    assert len(rows) == len(set(rows))
    assert all("\n" not in row for row in rows)
    return next(row for row in rows if "$(touch never)" in row)


launcher.choose = select_file
launcher.run()
assert len(calls) == 1 and calls[0][0][0:2] == ["gio", "open"]
assert "%0A" in calls[0][0][2] and calls[0][1] == {"start_new_session": True}
assert not (home / "never").exists()
calls.clear()
launcher.choose = lambda rows, prompt, monitor=None: next(row for row in rows if "[Aplicación]" in row)
launcher.run()
assert calls == ["app"]
calls.clear()
launcher.choose = lambda rows, prompt, monitor=None: None
launcher.run()
assert not calls
launcher.choose = lambda rows, prompt, monitor=None: "Cancelar"
launcher.execute_action("Apagar")
assert not calls
launcher.choose = lambda rows, prompt, monitor=None: "Confirmar"
launcher.execute_action("Apagar")
assert calls[0][0] == ["systemctl", "poweroff"]
calls.clear()
os.environ.pop("XDG_SESSION_ID", None)
launcher.execute_action("Cerrar sesión")
assert not calls
Path.home = original_home
subprocess.Popen = original_popen
launcher.choose = actual_choose
print("PASS: dynamic file index, hostile names, exact menu mapping, GIO launch and action confirmation")
