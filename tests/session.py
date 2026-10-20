"""Exercise the supervisor with inert process/bus/clock/monitor doubles only."""
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
connected = "DP-1 connected primary 1920x1080+0+0\nHDMI-1 disconnected\n"
secondary = "DP-1 connected 1920x1080+0+0\nHDMI-1 connected primary 1280x720+1920+0\n"
geometry = "DP-1 connected primary 1280x720+0+0\nHDMI-1 disconnected\n"

tray_config = dict(line.split(" = ", 1) for line in
                   (module.DATA / "tint2rc").read_text().splitlines()
                   if line and not line.startswith("#"))
for key, value in {"panel_items": "S", "panel_monitor": "primary",
                   "panel_position": "bottom right horizontal",
                   "panel_size": "100% 24", "panel_shrink": "1",
                   "panel_dock": "1", "strut_policy": "none",
                   "systray_monitor": "primary", "systray_icon_size": "20"}.items():
    assert tray_config[key] == value
inventory = (root / "scripts/dependencies.tsv").read_text()
assert "command\ttint2\ttint2\t/usr/bin/tint2\n" in inventory
assert "nitrogen" not in inventory and "trayer" not in inventory


class Process:
    def __init__(self, owner, argv):
        self.owner, self.args = owner, argv
        self.pid = 900000 + len(owner.processes)
        self.returncode = None
        self.polls = 0
        self.waits = 0
        self.environment = dict(os.environ)
        owner.processes.append(self)

    def poll(self):
        if self.args[0].endswith("/dwm"):
            self.polls += 1
            if self.polls > 2:
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
        self.randr = [connected]

    def run(self, argv, **kwargs):
        self.calls.append(argv)
        assert kwargs.get("timeout") == 20
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
        elif name == "xrandr":
            assert argv == [name, "--query"]
            output = self.randr[0]
            if len(self.randr) > 1:
                self.randr.pop(0)
        elif name == "xsetroot":
            assert argv == [name, "-solid", "#f6f5f4"]
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
        return Process(self, argv)

    def kill(self, pid, sig):
        assert pid in [p.pid for p in self.processes], ("foreign process", pid)
        self.kills.append((pid, sig))

    def sleep(self, seconds):
        if seconds == 2 and self.interrupt is not None:
            self.handlers[self.interrupt](self.interrupt, None)

    def signal(self, sig, handler):
        previous = self.handlers.get(sig, signal.SIG_DFL)
        self.handlers[sig] = handler
        return previous


original = (subprocess.run, subprocess.Popen, os.killpg, signal.signal,
            module.time.sleep, Path.is_socket)
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
    os.killpg, signal.signal, module.time.sleep = world.kill, world.signal, world.sleep
    Path.is_socket = lambda path: world.agent and path == runtime / "gcr/ssh"
    return runtime


def exercise(world, failure=False, setup=None):
    runtime = configure(world)
    if setup:
        setup(runtime)
    try:
        module.run()
        assert not failure, "expected session failure"
    except (RuntimeError, OSError, KeyError):
        assert failure, "unexpected session failure"
    assert {p.pid for p in world.processes} == {pid for pid, sig in world.kills}
    assert all(handler == signal.SIG_DFL for handler in world.handlers.values())
    return runtime


try:
    world = World()
    exercise(world)
    spawned = [p.args[0] for p in world.processes]
    assert spawned[:-2] == ["dunst", "picom", "lxqt-policykit-agent", "tint2", "snixembed", "nm-applet", "copyq", "xss-lock"]
    assert spawned[-2].endswith("/dwm")
    assert spawned[-1].endswith("/wm-displays")
    assert world.processes[-1].args[1:] == ["--watch"]
    assert world.processes[-1].environment["SSH_AUTH_SOCK"] == "/synthetic/foreign-agent"
    assert "lxqt-config-monitor" not in inventory
    assert not any(c[0] == "systemctl" for c in world.calls)
    locker = next(p for p in world.processes if p.args[0] == "xss-lock")
    assert locker.args == ["xss-lock", "--transfer-sleep-lock", "--", "i3lock", "--nofork"]
    assert ["xset", "s", "600", "600"] in world.calls
    assert ["xsetroot", "-solid", "#f6f5f4"] in world.calls
    assert next(p.args for p in world.processes if p.args[0] == "tint2") == [
        "tint2", "-c", str(module.DATA / "tint2rc")]
    assert not any(c[0] in ("loginctl", "powerdevil", "pactl", "wpctl") for c in world.calls)

    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        world = World()
        world.interrupt = sig
        exercise(world)
    for field, value in (("dead", "lxqt-policykit-agent"), ("dead", "tint2"),
                         ("fail_spawn", "tint2"), ("fail_spawn", "nm-applet"),
                         ("fail_command", "xrandr"),
                         ("dead", str(root / "scripts/wm-displays")),
                         ("fail_spawn", str(root / "scripts/wm-displays")), ("wm_code", 2),
                         ("foreign", True), ("existing_wm", True)):
        world = World()
        setattr(world, field, value)
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
    module.DATA = temporary / "missing-tray-config"
    module.DATA.mkdir()
    for config in ("dunstrc", "picom.conf"):
        (module.DATA / config).write_text("synthetic")
    try:
        world = World()
        exercise(world, failure=True)
        assert not world.calls and not world.processes
    finally:
        module.DATA = data

    # The display manager owns profiles; the supervisor only tracks tray geometry.
    # Focus never enters this interface.
    world = World()
    configure(world)
    children = []
    previous, tray = module.monitors(None, None, children, None)
    first = tray
    previous, tray = module.monitors(previous, tray, children, None)
    assert tray is first
    world.randr = [geometry]
    previous, tray = module.monitors(previous, tray, children, None)
    assert tray is not first and first.pid in [pid for pid, sig in world.kills]
    assert all(c[0] == "xrandr" for c in world.calls)
    for text in (secondary, connected, secondary):
        world.randr = [text]
        previous, tray = module.monitors(previous, tray, children, None)
    assert all(c[0] == "xrandr" for c in world.calls)
    assert len(children) == 1 and children[0][0] is tray
    assert tray.args == ["tint2", "-c", str(module.DATA / "tint2rc")]
    # A primary-only change also restarts the tray without reapplying profiles.
    first = tray
    world.randr = [secondary.replace("DP-1 connected ", "DP-1 connected primary ")
                   .replace("HDMI-1 connected primary ", "HDMI-1 connected ")]
    previous, tray = module.monitors(previous, tray, children, None)
    assert tray is not first and first.pid in [pid for pid, sig in world.kills]
    assert all(c[0] == "xrandr" for c in world.calls)
    assert module.outputs(secondary)[0] != module.outputs(connected)[0]
    try:
        module.outputs("invalid synthetic output")
        raise AssertionError("invalid RandR accepted")
    except RuntimeError:
        pass
    print("PASS: session startup, DISPLAY lock, signals, cleanup, shared agents, monitors and locking (all commands mocked)")
finally:
    (subprocess.run, subprocess.Popen, os.killpg, signal.signal,
     module.time.sleep, Path.is_socket) = original
    os.environ.clear()
    os.environ.update(environment)
