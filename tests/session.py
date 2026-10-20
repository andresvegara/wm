"""Exercise the supervisor with inert process/bus/clock/monitor doubles only."""
from datetime import datetime
import fcntl
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import types

root, temporary = map(Path, sys.argv[1:])
module = types.ModuleType("supervisor")
module.__file__ = str(root / "scripts/wm-supervisor")
exec(compile(Path(module.__file__).read_text(), module.__file__, "exec"), module.__dict__)
module.DATA = root / "session"
clockvalue = datetime(2026, 10, 20, 3, 4, 5)
inventory = (root / "scripts/dependencies.tsv").read_text()
assert "tint2" not in inventory and not (module.DATA / "tint2rc").exists()
assert "pc\txrandr\tlibxrandr\txrandr.pc\n" in inventory
assert "nitrogen" not in inventory and "trayer" not in inventory


class Process:
    def __init__(self, owner, argv, env=None):
        self.owner, self.args = owner, argv
        self.pid = 900000 + len(owner.processes)
        self.returncode = None
        self.polls = 0
        self.waits = 0
        self.environment = dict(os.environ if env is None else env)
        owner.processes.append(self)

    def poll(self):
        if self.args[0].endswith("/dwm"):
            self.polls += 1
            if self.polls > self.owner.wm_lifetime:
                self.returncode = self.owner.wm_code
        elif self.args[0] == self.owner.dead:
            self.returncode = 3
        return self.returncode

    def wait(self, timeout):
        self.waits += 1
        if self.owner.stubborn and self.waits == 1:
            raise subprocess.TimeoutExpired(self.args, timeout)
        self.returncode = 0
        return 0


class World:
    def __init__(self):
        self.processes, self.calls, self.kills, self.handlers = [], [], [], {}
        self.dead = self.fail_spawn = self.fail_command = None
        self.foreign = self.existing_wm = self.stubborn = False
        self.secret = True
        self.agent = False
        self.no_agent = self.no_secrets = False
        self.wm_code = 0
        self.interrupt = None
        self.tray_output = None
        self.tray_timeout = False
        self.tray_code = 0
        self.wm_lifetime = 2
        self.sleeps = []

    def run(self, argv, **kwargs):
        self.calls.append(argv)
        assert kwargs.get("timeout") == (1 if argv[0] == "xprop" else 20)
        name = argv[0]
        code, output = 0, ""
        if name == self.fail_command:
            raise OSError("synthetic failure")
        if name == "wmctrl":
            assert argv == ["wmctrl", "-m"]
            code = 0 if self.existing_wm else 1
        elif name == "gdbus":
            assert argv[-1] in ("org.freedesktop.Notifications", "org.kde.StatusNotifierWatcher", "org.freedesktop.secrets")
            if argv[-1] == "org.freedesktop.secrets":
                owned = self.secret
            else:
                executable = "dunst" if argv[-1] == "org.freedesktop.Notifications" else "snixembed"
                owned = self.foreign or any(p.args[0] == executable for p in self.processes)
            output = "(true,)" if owned else "(false,)"
        elif name == "systemctl":
            assert argv in (["systemctl", "--user", "start", "gnome-keyring-daemon.socket"],
                            ["systemctl", "--user", "start", "gcr-ssh-agent.socket"])
            if argv[-1] == "gcr-ssh-agent.socket":
                self.agent = not self.no_agent
        elif name == "gnome-keyring-daemon":
            assert argv == [name, "--start", "--components=secrets"]
            self.secret = not self.no_secrets
        elif name == "xprop":
            assert argv == [name, "-root", "_WM_SYSTRAY"]
            if self.tray_timeout:
                raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
            code = self.tray_code
            wm = next(p for p in self.processes if p.args[0].endswith("/dwm"))
            assert not any(p.args[0] == "snixembed" for p in self.processes)
            output = self.tray_output if self.tray_output is not None else (
                "_WM_SYSTRAY(CARDINAL) = {}, 50\n".format(wm.pid))
        elif name == "setxkbmap":
            assert argv == [name, "-layout", "es", "-variant", ""]
            assert not self.processes
        elif name == "xsetroot":
            assert argv in ([name, "-solid", "#f6f5f4", "-name", clockvalue.strftime("%Y-%m-%d %H:%M:%S")],
                            [name, "-name", clockvalue.strftime("%Y-%m-%d %H:%M:%S")])
        elif name == "xset":
            assert argv == [name, "s", "600", "600"]
        else:
            raise AssertionError(("unmocked command", argv))
        return types.SimpleNamespace(returncode=code, stdout=output)

    def popen(self, argv, **kwargs):
        assert kwargs["start_new_session"] is True
        assert kwargs["stdin"] == subprocess.DEVNULL
        if argv[0] == self.fail_spawn:
            raise OSError("synthetic spawn failure")
        return Process(self, argv, kwargs.get("env"))

    def kill(self, pid, sig):
        assert pid in [p.pid for p in self.processes], ("foreign process", pid)
        self.kills.append((pid, sig))

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        if seconds == 1 and self.interrupt is not None:
            self.handlers[self.interrupt](self.interrupt, None)

    def signal(self, sig, handler):
        previous = self.handlers.get(sig, signal.SIG_DFL)
        self.handlers[sig] = handler
        return previous


original = (subprocess.run, subprocess.Popen, os.killpg, signal.signal,
            module.time, Path.is_socket)
environment = dict(os.environ)
serial = 0


def configure(world):
    global serial
    serial += 1
    folder = temporary / ("session-" + str(serial))
    folder.mkdir(mode=0o700)
    runtime = folder / "runtime"
    runtime.mkdir(mode=0o700)
    os.environ.clear()
    os.environ.update(HOME=str(folder), XDG_RUNTIME_DIR=str(runtime),
                      XDG_CACHE_HOME=str(folder / "cache"), DISPLAY=":synthetic",
                      XDG_SESSION_TYPE="x11", DBUS_SESSION_BUS_ADDRESS="mock:bus",
                      SSH_AUTH_SOCK="/synthetic/foreign-agent")
    subprocess.run, subprocess.Popen = world.run, world.popen
    os.killpg, signal.signal = world.kill, world.signal
    Path.is_socket = lambda path: world.agent and path == runtime / "gcr/ssh"
    module.time = types.SimpleNamespace(sleep=world.sleep,
                                       strftime=lambda format: clockvalue.strftime(format))
    return runtime


def exercise(world, failure=False, setup=None):
    runtime = configure(world)
    if setup:
        setup(runtime)
    try:
        module.run()
        assert not failure, "expected session failure"
    except (RuntimeError, OSError, KeyError, subprocess.SubprocessError):
        assert failure, "unexpected session failure"
    assert {p.pid for p in world.processes} == {pid for pid, sig in world.kills}
    assert all(handler == signal.SIG_DFL for handler in world.handlers.values())
    return runtime


try:
    world = World()
    exercise(world)
    spawned = [p.args[0] for p in world.processes]
    assert spawned[0].endswith("/dwm")
    assert spawned[1:-1] == ["dunst", "picom", "lxqt-policykit-agent", "snixembed", "cbatticon", "pasystray", "nm-applet", "copyq", "xss-lock"]
    assert any(call[0] == "xprop" for call in world.calls)
    assert not any(call[0] == "xrandr" for call in world.calls)
    assert spawned[-1].endswith("/wm-displays")
    assert world.processes[-1].args[1:] == ["--watch"]
    assert world.processes[-1].environment["SSH_AUTH_SOCK"] == "/synthetic/foreign-agent"
    assert "lxqt-config-monitor" not in inventory
    battery = next(p for p in world.processes if p.args[0] == "cbatticon")
    volume = next(p for p in world.processes if p.args[0] == "pasystray")
    assert battery.args == ["cbatticon"]
    assert volume.args == ["pasystray", "--notify=none", "--volume-max=100"]
    assert volume.environment["PULSE_CLIENTCONFIG"] == str(module.DATA / "pulse-client.conf")
    assert all("PULSE_CLIENTCONFIG" not in p.environment for p in world.processes if p is not volume)
    assert "autospawn = no" in (module.DATA / "pulse-client.conf").read_text()
    assert "command\tcbatticon\tcbatticon\t/usr/bin/cbatticon\n" in inventory
    assert "command\tpasystray\tpasystray\t/usr/bin/pasystray\n" in inventory
    assert not any(c[0] == "systemctl" for c in world.calls)
    locker = next(p for p in world.processes if p.args[0] == "xss-lock")
    assert locker.args == ["xss-lock", "--transfer-sleep-lock", "--", "i3lock", "--nofork"]
    assert ["xset", "s", "600", "600"] in world.calls
    assert ["xsetroot", "-solid", "#f6f5f4", "-name", "2026-10-20 03:04:05"] in world.calls
    assert ["xsetroot", "-name", "2026-10-20 03:04:05"] in world.calls
    assert 1 in world.sleeps and 2 not in world.sleeps
    assert ["setxkbmap", "-layout", "es", "-variant", ""] in world.calls
    assert not any(c[0] in ("loginctl", "powerdevil", "pactl", "wpctl") for c in world.calls)

    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        world = World()
        world.interrupt = sig
        exercise(world)
    world = World()
    world.fail_command = "setxkbmap"
    exercise(world, failure=True)
    assert not world.processes and not any(call[0] == "systemctl" for call in world.calls)

    for field, value in (("dead", "lxqt-policykit-agent"),
                         ("fail_spawn", str(root / "scripts/dwm")), ("fail_spawn", "nm-applet"),
                         ("fail_command", "xprop"), ("fail_command", "xsetroot"),
                         ("dead", str(root / "scripts/wm-displays")),
                         ("fail_spawn", str(root / "scripts/wm-displays")), ("wm_code", 2),
                         ("foreign", True), ("existing_wm", True)):
        world = World()
        setattr(world, field, value)
        exercise(world, failure=True)
    for name in ("cbatticon", "pasystray"):
        world = World()
        world.dead = name
        exercise(world)
        assert sum(p.args[0] == name for p in world.processes) == 1
        world = World()
        world.fail_spawn = name
        exercise(world, failure=True)

    world = World()
    world.stubborn = True
    exercise(world)
    assert any(sig == signal.SIGKILL for pid, sig in world.kills)

    world = World()
    world.secret = False
    exercise(world, setup=lambda runtime: os.environ.pop("SSH_AUTH_SOCK"))
    assert world.processes[-1].environment["SSH_AUTH_SOCK"].endswith("/gcr/ssh")
    assert ["gnome-keyring-daemon", "--start", "--components=secrets"] in world.calls

    world = World()
    world.no_agent = True
    exercise(world, failure=True, setup=lambda runtime: os.environ.pop("SSH_AUTH_SOCK"))
    world = World()
    world.secret = False
    world.no_secrets = True
    exercise(world, failure=True)

    for variable in ("DISPLAY", "DBUS_SESSION_BUS_ADDRESS"):
        exercise(World(), failure=True, setup=lambda runtime, key=variable: os.environ.pop(key))
    exercise(World(), failure=True, setup=lambda runtime: runtime.chmod(0o755))
    world = World()
    runtime = configure(world)
    key = hashlib.sha256(os.environ["DISPLAY"].encode()).hexdigest()[:16]
    directory = runtime / ("wm-" + key)
    directory.mkdir(mode=0o700)
    with (directory / "session.lock").open("a") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            module.run()
            raise AssertionError("duplicate DISPLAY admitted")
        except RuntimeError:
            pass
    assert not world.processes

    # Missing defaults fail before any commands or children, without touching sources.
    data = module.DATA
    module.DATA = temporary / "missing-picom-config"
    module.DATA.mkdir()
    (module.DATA / "dunstrc").write_text("synthetic")
    try:
        world = World()
        exercise(world, failure=True)
        assert not world.calls and not world.processes
    finally:
        module.DATA = data

    module.DATA = temporary / "missing-pulse-config"
    module.DATA.mkdir()
    for config in ("dunstrc", "picom.conf"):
        (module.DATA / config).write_text("synthetic")
    try:
        world = World()
        exercise(world, failure=True)
        assert not world.calls and not world.processes
    finally:
        module.DATA = data

    # Stale, foreign and malformed readiness must never start tray applets.
    for output in ("_WM_SYSTRAY: not found", "_WM_SYSTRAY(CARDINAL) = 1, 50",
                   "_WM_SYSTRAY(CARDINAL) = 900000, 0", "_WM_SYSTRAY(STRING) = 900000, 50"):
        world = World()
        world.tray_output = output
        world.wm_lifetime = 1000
        exercise(world, failure=True)
        assert len(world.processes) == 1
        assert sum(call[0] == "xprop" for call in world.calls) == 50
    world = World()
    world.tray_timeout = True
    exercise(world, failure=True)
    assert len(world.processes) == 1
    world = World()
    world.tray_code = 1
    world.wm_lifetime = 1000
    exercise(world, failure=True)
    assert len(world.processes) == 1
    # An early dwm exit stops readiness before starting any applets.
    world = World()
    world.tray_output = "not ready"
    world.wm_lifetime = 0
    exercise(world, failure=True)
    assert len(world.processes) == 1 and not any(call[0] == "xprop" for call in world.calls)
    clockvalue = datetime(2026, 10, 20, 23, 59, 59)
    world = World()
    exercise(world)
    assert ["xsetroot", "-name", "2026-10-20 23:59:59"] in world.calls
    print("PASS: native tray readiness, clock, startup, DISPLAY lock, cleanup and agents (all commands mocked)")
finally:
    (subprocess.run, subprocess.Popen, os.killpg, signal.signal,
     module.time, Path.is_socket) = original
    os.environ.clear()
    os.environ.update(environment)
