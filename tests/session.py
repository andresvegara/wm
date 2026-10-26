"""Real dwm supervisor with synthetic process, bus, RandR and XSettings boundaries."""
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import types
from unittest.mock import patch
from contextlib import redirect_stderr

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
        if name == "dwm" and self.world.ticks >= self.world.wm_ticks:
            self.returncode = self.world.wm_code
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
        self.wm_ticks, self.wm_code = 2, 0
        self.interrupt_at = self.logout_at = None
        self.logout_session = "synthetic"
        self.spawn_attempts = []
        self.version = "4.20.0"
        self.wallpaper_status = 0
        self.health_samples = []
        self.notification_status = 0

    def popen(self, argv, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["stderr"] == subprocess.STDOUT and kwargs["start_new_session"]
        self.spawn_attempts.append((Path(argv[0]).name, self.clock))
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
            assert any(name == "dunst" for name, clock in self.spawn_attempts)
            code = self.wallpaper_status
        elif name == "xset":
            assert argv == [name, "s", "600", "600"]
        elif name == "notify-send":
            assert kwargs["timeout"] == 2
            assert argv[1:4] == ["--app-name=wm-session", "--urgency=normal", "--expire-time=10000"]
            assert argv[-2] == "Incidencias de sesión" and "Estado de sesión" in argv[-1]
            assert any(p.args[0] == "dunst" and p.poll() is None for p in self.processes)
            code = self.notification_status
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
            path = Path(os.environ["WM_DWM_RUNTIME"]) / "health.json"
            if path.exists():
                self.health_samples.append(json.loads(path.read_text()))
            if self.ticks == self.interrupt_at:
                self.handlers[signal.SIGTERM](signal.SIGTERM, None)
            if self.ticks == self.logout_at:
                module.write_private(Path(os.environ["WM_DWM_RUNTIME"]) / "logout", self.logout_session)

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
    if world.processes:
        assert not next(runtime.glob("wm-*/session.id"), None)
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
complements = ("xfce4-power-manager", "xsettingsd", "dunst", "snixembed", "picom",
               "lxqt-policykit-agent", "dwmblocks", "nm-applet", "copyq", "wm-displays")
for name in complements:
    for failure in ("exit_child", "fail_command", "late_child"):
        world = World()
        setattr(world, failure, name)
        folder = exercise(world)
        logfile = next((folder / "cache/wm").glob("*.log"))
        assert name in logfile.read_text(), (name, failure)
        assert world.ticks == world.wm_ticks, "complement closed dwm"
world = World()
world.exit_child = "xss-lock"
exercise(world, error=True)
assert not any(argv[0] == "xfconf-query" for argv in world.calls)
assert not any(p.args[0] == "xfce4-power-manager" for p in world.processes)
for attribute in ("bad_inhibitor", "bad_bus", "bad_inhibitor_reply"):
    world = World()
    setattr(world, attribute, True)
    exercise(world, error=True)
    assert not any(argv[0] == "xfconf-query" for argv in world.calls)
    assert not any(p.args[0] == "xfce4-power-manager" for p in world.processes)
for name in ("wm-appearance", "setxkbmap", "wm-keyboard"):
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
    exercise(world)
    assert not any(p.args[0] == "xfce4-power-manager" for p in world.processes)
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
exercise(world)
world = World()
world.late_child = "xss-lock"
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
# Recovery is bounded even for persistent crashes, readiness and spawn failures.
for failure in ("exit_child", "late_child", "fail_command"):
    for name in complements:
        world = World()
        world.wm_ticks = 35
        setattr(world, failure, name)
        exercise(world)
        attempts = [clock for command, clock in world.spawn_attempts if command == name]
        if name == "xfce4-power-manager" and failure == "fail_command":
            assert not attempts  # Version/config prerequisite failed: power stays off.
        else:
            assert len(attempts) == (1 if name == "xsettingsd" else 4), (name, failure, attempts)
            assert all(b - a >= 5 for a, b in zip(attempts, attempts[1:]))

# A transient Dunst crash recovers without losing the WM or its later children.
world = World()
world.wm_ticks = 15
original_poll = Process.poll
def transient_poll(process):
    if process.args[0] == "dunst" and world.ticks >= 1:
        notes = [p for p in world.processes if p.args[0] == "dunst"]
        if process is notes[0]:
            process.returncode = 1
    return original_poll(process)
with patch.object(Process, "poll", transient_poll):
    folder = exercise(world)
assert len([p for p in world.processes if p.args[0] == "dunst"]) == 2
assert "reinicio 1/3 de dunst" in next((folder / "cache/wm").glob("*.log")).read_text()
assert any("dunst" in sample["issues"] for sample in world.health_samples)
assert not world.health_samples[-1]["issues"], "recovered Dunst still degraded"
notes = [argv for argv in world.calls if argv[0] == "notify-send"]
assert len(notes) == 1 and "dunst" in notes[0][-1], "lost deferred notice or spammed retries"

world = World()
world.fail_command = "xfconf-query"
exercise(world)
assert not any(p.args[0] == "xfce4-power-manager" for p in world.processes)
world = World()
world.secrets = False
world.fail_command = "gnome-keyring-daemon"
exercise(world)
world = World()
world.fail_command = "systemctl"
exercise(world, agent=False)
world = World()
world.wm_code = 9
exercise(world, error=True)
world = World()
world.wm_ticks, world.interrupt_at = 100, 1
exercise(world)
assert world.ticks == 1

# Logout asks our supervisor to finish, never kills the SDDM helper.
world = World()
world.wm_ticks, world.logout_at = 100, 1
exercise(world)
assert world.ticks == 1
world = World()
world.wm_ticks, world.logout_at, world.logout_session = 3, 1, "another-session"
exercise(world)
assert world.ticks == 3, "foreign session request closed dwm"
def stale_logout(data, env):
    directory = Path(env["XDG_RUNTIME_DIR"]) / ("wm-" + key)
    directory.mkdir(mode=0o700)
    module.write_private(directory / "logout", "synthetic")
world = World()
exercise(world, prepare=stale_logout)
assert world.ticks == world.wm_ticks

# Failed complement cleanup disables its retries, not the desktop.
for failure in ("exit_child", "late_child"):
    world = World()
    world.wm_ticks = 12
    setattr(world, failure, "dunst")
    original_stop = module.stop
    failed = []
    def fail_cleanup(process):
        if process.args[0] == "dunst" and not failed:
            failed.append(True)
            raise OSError("synthetic cleanup failure")
        original_stop(process)
    with patch.object(module, "stop", side_effect=fail_cleanup):
        folder = exercise(world)
    assert world.ticks == 12 and len([p for p in world.processes if p.args[0] == "dunst"]) == 1
    assert "synthetic cleanup failure" in next((folder / "cache/wm").glob("*.log")).read_text()

# Previous session evidence survives the next startup, with private file checks.
def previous_log(data, env):
    cache = Path(env["XDG_CACHE_HOME"]) / "wm"
    cache.mkdir(mode=0o700, parents=True)
    path = cache / ("session-" + key + ".log")
    path.write_text("synthetic previous failure\n")
    path.chmod(0o600)
folder = exercise(World(), prepare=previous_log)
archive = next((folder / "cache/wm").glob("*.log.previous"))
assert archive.read_text() == "synthetic previous failure\n"
assert archive.stat().st_mode & 0o777 == 0o600
for kind in ("symlink", "hardlink", "permissions"):
    def unsafe_archive(data, env):
        previous_log(data, env)
        cache = Path(env["XDG_CACHE_HOME"]) / "wm"
        archive = cache / ("session-" + key + ".log.previous")
        sentinel = data / "sentinel"
        sentinel.write_text("untouched")
        sentinel.chmod(0o600)
        if kind == "symlink":
            archive.symlink_to(sentinel)
        elif kind == "hardlink":
            os.link(sentinel, archive)
        else:
            archive.write_text("untouched")
            archive.chmod(0o644)
    world = World()
    folder = exercise(world, error=True, prepare=unsafe_archive)
    assert not world.processes and (folder / "data/sentinel").read_text() == "untouched"
    assert next((folder / "cache/wm").glob("*.log")).read_text() == "synthetic previous failure\n"

# Health stays visible for exhausted services; repeated retries do not spam.
world = World()
world.wm_ticks, world.exit_child = 35, "picom"
exercise(world)
assert "deshabilitado" in world.health_samples[-1]["issues"]["picom"]
assert len([argv for argv in world.calls if argv[0] == "notify-send"]) == 1
assert all(len(json.dumps(sample).encode()) <= 4096 for sample in world.health_samples)
# A component that repeatedly survives only one cycle is one problem episode.
world = World()
world.wm_ticks = 35
born = {}
def flapping_poll(process):
    if process.args[0] == "picom":
        born.setdefault(process.pid, world.ticks)
        if world.ticks > born[process.pid]:
            process.returncode = 1
    return original_poll(process)
with patch.object(Process, "poll", flapping_poll):
    exercise(world)
assert len([argv for argv in world.calls if argv[0] == "notify-send"]) == 1
assert "deshabilitado" in world.health_samples[-1]["issues"]["picom"]
world = World()
world.wm_ticks, world.exit_child = 35, "dunst"
exercise(world)
assert "dunst" in world.health_samples[-1]["issues"]
assert not any(argv[0] == "notify-send" for argv in world.calls), "activated absent Dunst"
for failure in ("notify-send", None):
    world = World()
    world.wm_ticks, world.exit_child = 15, "picom"
    world.fail_command = failure
    world.notification_status = 1
    folder = exercise(world)
    assert "picom" in world.health_samples[-1]["issues"]
    assert len([argv for argv in world.calls if argv[0] == "notify-send"]) == 1
    assert "aviso no disponible" in next((folder / "cache/wm").glob("*.log")).read_text()

world = World()
world.wm_ticks = 15
original_write = module.write_private
def fail_health(path, content):
    if path.name == "health.json":
        raise OSError("synthetic status publication failure")
    original_write(path, content)
with patch.object(module, "write_private", side_effect=fail_health):
    folder = exercise(world)
assert world.ticks == 15
assert next((folder / "cache/wm").glob("*.log")).read_text().count("no se pudo publicar estado") == 1

for issues in ({}, {"dunst": "No disponible; recuperación 1/3"}):
    with patch.object(module, "session_health", return_value=issues), patch.object(module, "choose") as menu:
        assert module.main(["--status"]) == 0
        rows, prompt = menu.call_args.args
        assert prompt == "Estado de sesión" and rows
        assert ("dunst" in rows[0]) == bool(issues)
with patch.object(module, "session_health", side_effect=RuntimeError("synthetic unavailable")), \
     patch.object(module, "choose") as menu:
    assert module.main(["--status"]) == 0 and "Estado no disponible" in menu.call_args.args[0][0]

# SDDM must receive a session error (2), never its reserved auth-error status (1).
with patch.object(module, "run", side_effect=RuntimeError("synthetic failure")), \
     patch.object(subprocess, "run", side_effect=AssertionError("NO GUI")), \
     redirect_stderr(io.StringIO()) as errors:
    assert module.main([]) == 2 and "synthetic failure" in errors.getvalue()
with patch.object(module, "run", return_value=None):
    assert module.main([]) == 0

request = temporary / "logout-request"
request.mkdir(mode=0o700)
module.write_private(request / "session.id", "synthetic")
with patch.dict(os.environ, WM_DWM_RUNTIME=str(request), XDG_SESSION_ID="synthetic"), \
     patch.object(subprocess, "run", side_effect=AssertionError("NO SESSION COMMANDS")):
    assert module.main(["--logout"]) == 0
    assert module.read_private(request / "logout") == "synthetic"
    (request / "logout").unlink()
    for session in ("", "foreign"):
        with patch.dict(os.environ, XDG_SESSION_ID=session), redirect_stderr(io.StringIO()):
            assert module.main(["--logout"]) == 2
            assert not (request / "logout").exists()
    sentinel = request / "sentinel"
    sentinel.write_text("untouched")
    (request / "logout").symlink_to(sentinel)
    with redirect_stderr(io.StringIO()):
        assert module.main(["--logout"]) == 2
    assert sentinel.read_text() == "untouched"
print("PASS: supervisor degradation, bounded recovery, locker security, SDDM status, private logs and owned cleanup (all boundaries mocked)")
