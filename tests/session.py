"""Real dwm supervisor with synthetic process, bus, RandR and XSettings boundaries."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import types
from unittest.mock import patch

root, temporary = map(Path, sys.argv[1:])
sys.path.insert(0, str(root / "scripts"))
module = types.ModuleType("supervisor")
module.__file__ = str(root / "scripts/wm-supervisor")
exec(compile(Path(module.__file__).read_text(), module.__file__, "exec"), module.__dict__)


class Process:
    def __init__(self, world, argv):
        self.world, self.args = world, argv
        self.pid = 1000 + len(world.processes)
        self.returncode = None
        self.waited = False

    def poll(self):
        name = Path(self.args[0]).name
        if name == self.world.exit_child or (self.world.late_child == name and self.world.ticks):
            self.returncode = 1
        if name == "dwm" and self.world.ticks >= 2:
            self.returncode = 0
        return self.returncode

    def wait(self, timeout):
        assert timeout == 3
        if self.world.slow_child == Path(self.args[0]).name and not self.waited:
            self.waited = True
            raise subprocess.TimeoutExpired(self.args, timeout)
        self.returncode = 0
        return 0


class World:
    def __init__(self):
        self.processes, self.calls, self.kills = [], [], []
        self.handlers, self.ticks = {}, 0
        self.exit_child = self.late_child = self.fail_command = self.slow_child = None
        self.conflict = None
        self.pref_exists, self.secrets = True, True
        self.bad_tray, self.bad_ownership, self.bad_inhibitor = False, False, False
        self.bad_bus, self.bad_inhibitor_reply = False, False
        self.clock = 0
        self.version = "4.20.0"
        self.wallpaper_status = 0

    def popen(self, argv, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["stderr"] == subprocess.STDOUT and kwargs["start_new_session"]
        if Path(argv[0]).name == self.fail_command:
            raise OSError("synthetic spawn failure")
        process = Process(self, argv)
        self.processes.append(process)
        return process

    def run(self, argv, **kwargs):
        self.calls.append(argv)
        name = Path(argv[0]).name
        if name == self.fail_command:
            raise OSError("synthetic command failure")
        code, output = 0, ""
        if name == "wmctrl":
            assert argv == ["wmctrl", "-m"]
            code = 1
        elif name == "gdbus":
            target = argv[-1]
            owned = target == self.conflict or target == "org.freedesktop.secrets" and self.secrets
            owned |= any({"dunst": "org.freedesktop.Notifications", "snixembed": "org.kde.StatusNotifierWatcher",
                          "xfce4-power-manager": "org.xfce.PowerManager"}.get(Path(p.args[0]).name) == target
                         for p in self.processes)
            output = "invalid" if self.bad_bus else "(true,)" if owned else "(false,)"
        elif name == "xprop":
            assert argv == ["xprop", "-root", "_WM_SYSTRAY"]
            wm = next(p for p in self.processes if Path(p.args[0]).name == "dwm")
            output = "garbage" if self.bad_tray else "_WM_SYSTRAY(CARDINAL) = {}, 50\n".format(wm.pid + self.bad_ownership)
        elif name == "xfce4-power-manager":
            assert argv == [name, "--version"]
            output = "Xfce Power Manager " + self.version
        elif name == "busctl":
            assert kwargs["timeout"] == 1 and argv[-1] == "ListInhibitors"
            locker = next(p for p in self.processes if p.args[0] == "xss-lock")
            output = json.dumps({"type": "a(ssssuu)", "data": [[["sleep", "xss-lock", "lock", "delay",
                                  os.getuid(), locker.pid + int(self.bad_inhibitor)]]]})
            if self.bad_inhibitor_reply:
                output = '{"type":"a(ssssuu)","data":["bad"]}'
        elif name == "xfconf-query":
            if "--create" not in argv:
                code, output = (0, "balanced") if self.pref_exists else (1, "")
        elif name == "setxkbmap":
            assert argv == [name, "-layout", "es,us", "-variant", ","] and not self.processes
        elif name == "wm-keyboard":
            assert argv == [name, "--reset"] and not self.processes
        elif name == "wm-appearance":
            assert argv[1] in ("--prepare", "--apply-current")
        elif name == "xsetroot":
            assert argv == [name, "-solid", "#f6f5f4", "-name", "wm"]
        elif name == "wm-wallpaper":
            assert argv == [name, "--restore"]
            assert any(p.args[0] == "dunst" for p in self.processes)
            code = self.wallpaper_status
        elif name == "xset":
            assert argv == [name, "s", "600", "600"]
        elif name == "systemctl":
            assert argv in ([name, "--user", "start", "gnome-keyring-daemon.socket"],
                            [name, "--user", "start", "gcr-ssh-agent.socket"])
            self.secrets = True
        elif name == "gnome-keyring-daemon":
            assert argv == [name, "--start", "--components=secrets"]
        else:
            raise AssertionError(("UNMOCKED COMMAND", argv))
        return subprocess.CompletedProcess(argv, code, output, "")

    def kill(self, pid, sig):
        assert pid in {p.pid for p in self.processes}
        self.kills.append((pid, sig))

    def monotonic(self):
        self.clock += 0.01
        return self.clock

    def sleep(self, seconds):
        assert seconds in (1, 0.1)
        self.clock += seconds
        if seconds == 1:
            self.ticks += 1

    def handler(self, sig, handler):
        previous = self.handlers.get(sig, signal.SIG_DFL)
        self.handlers[sig] = handler
        return previous

    def owner(self):
        return 99 if self.conflict == "XSettings" or any(p.args[0] == "xsettingsd" for p in self.processes) else 0


counter = 0


def exercise(world, error=False, prepare=None, agent=True):
    global counter
    counter += 1
    folder = temporary / ("session-" + str(counter))
    folder.mkdir(mode=0o700)
    data = folder / "data"
    data.mkdir()
    for name in ("dunstrc", "picom.conf", "rofi.rasi", "themes.json"):
        (data / name).write_text("synthetic")
    runtime = folder / "runtime"
    runtime.mkdir(mode=0o700)
    environment = dict(XDG_RUNTIME_DIR=str(runtime), XDG_CACHE_HOME=str(folder / "cache"),
                       HOME=str(folder), DISPLAY=":synthetic", XDG_SESSION_TYPE="x11",
                       DBUS_SESSION_BUS_ADDRESS="mock:bus", XDG_SESSION_ID="synthetic")
    if agent:
        environment["SSH_AUTH_SOCK"] = "/synthetic/agent"
    if prepare:
        prepare(data, environment)
    with patch.dict(os.environ, environment, clear=True), patch.object(module, "DATA", data), \
         patch.object(subprocess, "run", side_effect=world.run), patch.object(subprocess, "Popen", side_effect=world.popen), \
         patch.object(os, "killpg", side_effect=world.kill), patch.object(signal, "signal", side_effect=world.handler), \
         patch.object(module.time, "sleep", side_effect=world.sleep), patch.object(module.time, "monotonic", side_effect=world.monotonic), \
         patch.object(module, "xsettings_owner", side_effect=world.owner), \
         patch.object(Path, "is_socket", autospec=True, side_effect=lambda path: path.name == "ssh"):
        try:
            module.run()
            assert not error, "expected failure"
        except (RuntimeError, OSError, KeyError, ValueError):
            assert error, "unexpected failure"
    assert {p.pid for p in world.processes} == {pid for pid, sig in world.kills}
    assert all(value == signal.SIG_DFL for value in world.handlers.values())
    return folder


world = World()
folder = exercise(world)
spawned = [Path(p.args[0]).name for p in world.processes]
assert spawned == ["xsettingsd", "dwm", "dunst", "picom", "lxqt-policykit-agent", "snixembed", "dwmblocks",
                   "nm-applet", "copyq", "xss-lock", "xfce4-power-manager", "wm-displays"]
assert world.processes[-2].args == ["xfce4-power-manager"]
assert world.processes[-1].args[1:] == ["--watch"]
assert world.processes[-3].args == ["xss-lock", "--transfer-sleep-lock", "--", "i3lock", "--nofork"]
assert [pid for pid, sig in world.kills] == [p.pid for p in reversed(world.processes)]
assert not any("power-auto" in p.args or "xfce4-screensaver" in p.args for p in world.processes)
setters = [argv for argv in world.calls if argv[0] == "xfconf-query" and "--create" in argv]
assert len(setters) == 4 and not any("profile-on-" in " ".join(argv) for argv in setters)
assert any("/general/LockCommand" in argv and argv[-1] == "wm-lock" for argv in setters)
assert any("/xfce4-power-manager/handle-brightness-keys" in argv and argv[-1] == "false" for argv in setters)
assert not any(argv[0] == "systemctl" for argv in world.calls)
for mode in ("failure", "missing"):
    world = World()
    if mode == "failure":
        world.wallpaper_status = 1
    else:
        world.fail_command = "wm-wallpaper"
    exercise(world)
    assert world.processes[-1].args[1:] == ["--watch"]
world = World()
world.pref_exists = False
exercise(world)
setters = [argv for argv in world.calls if "--create" in argv]
assert len(setters) == 6 and setters[-2][-1] == "performance" and setters[-1][-1] == "balanced"
for name in ("xfce4-power-manager", "xss-lock", "xsettingsd", "dunst", "snixembed"):
    world = World()
    world.exit_child = name
    exercise(world, error=True)
    if name == "xss-lock":
        assert not any(argv[0] == "xfconf-query" for argv in world.calls)
        assert not any(p.args[0] == "xfce4-power-manager" for p in world.processes)
for attribute in ("bad_inhibitor", "bad_bus", "bad_inhibitor_reply"):
    world = World()
    setattr(world, attribute, True)
    exercise(world, error=True)
    assert not any(argv[0] == "xfconf-query" for argv in world.calls)
    assert not any(p.args[0] == "xfce4-power-manager" for p in world.processes)
for name in ("xfconf-query", "wm-appearance", "setxkbmap", "wm-keyboard"):
    world = World()
    world.fail_command = name
    exercise(world, error=True)
    if name in ("setxkbmap", "wm-keyboard"):
        assert not world.processes
for name in ("org.freedesktop.Notifications", "org.xfce.PowerManager", "org.freedesktop.PowerManagement",
             "org.kde.Solid.PowerManagement", "XSettings"):
    world = World()
    world.conflict = name
    exercise(world, error=True)
    assert not world.processes
for version in ("4.18.0", "unreadable"):
    world = World(); world.version = version
    exercise(world, error=True)
    assert not world.processes
for missing in ("dunstrc", "picom.conf", "themes.json", "rofi.rasi"):
    world = World()
    exercise(world, error=True, prepare=lambda data, env: (data / missing).unlink())
    assert not world.processes
for variable in ("DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "XDG_SESSION_ID", "XDG_RUNTIME_DIR"):
    world = World()
    exercise(world, error=True, prepare=lambda data, env: env.pop(variable))
    assert not world.processes
world = World()
world.slow_child = "xfce4-power-manager"
exercise(world)
assert any(sig == signal.SIGKILL for pid, sig in world.kills)
world = World()
world.late_child = "xfce4-power-manager"
exercise(world, error=True)
for attr in ("bad_tray", "bad_ownership"):
    world = World()
    setattr(world, attr, True)
    exercise(world, error=True)
    assert [Path(p.args[0]).name for p in world.processes] == ["xsettingsd", "dwm"]
world = World()
world.secrets = False
exercise(world, agent=False)
assert any(argv[0] == "gnome-keyring-daemon" for argv in world.calls)
assert any("gcr-ssh-agent.socket" in argv for argv in world.calls)
key = hashlib.sha256(b":synthetic").hexdigest()[:16]
for kind in ("symlink", "hardlink", "permissions", "duplicate"):
    handles = []
    def unsafe(data, env):
        directory = Path(env["XDG_RUNTIME_DIR"]) / ("wm-" + key)
        directory.mkdir(mode=0o700)
        lock = directory / "session.lock"
        sentinel = data.parent / "sentinel"
        sentinel.write_text("untouched")
        sentinel.chmod(0o600)
        if kind == "symlink":
            lock.symlink_to(sentinel)
        elif kind == "hardlink":
            cache = Path(env["XDG_CACHE_HOME"]) / "wm"
            cache.mkdir(parents=True, mode=0o700)
            os.link(sentinel, cache / ("session-" + key + ".log"))
        elif kind == "permissions":
            directory.chmod(0o755)
        else:
            handle = lock.open("w")
            lock.chmod(0o600)
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            handles.append(handle)
    world = World()
    folder = exercise(world, error=True, prepare=unsafe)
    for handle in handles:
        handle.close()
    assert not world.processes and (folder / "sentinel").read_text() == "untouched"
print("PASS: real supervisor order, xfconf defaults/integration, exclusive locker, failures, conflicts, private locks/logs and owned cleanup (all boundaries mocked)")
