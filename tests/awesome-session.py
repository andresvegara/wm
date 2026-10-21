"""Exercise actual supervisor with inert process, bus, socket and signal doubles."""
import fcntl
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import types

root, temporary = map(Path, sys.argv[1:])
module = types.ModuleType("awesome_supervisor")
module.__file__ = str(root / "scripts/awesome-supervisor")
exec(compile(Path(module.__file__).read_text(), module.__file__, "exec"), module.__dict__)
data = temporary / "awesome-session-data"
(data / "awesome").mkdir(parents=True)
(data / "awesome/rc.lua").write_text("-- synthetic\n")
(data / "dunstrc").write_text("# synthetic\n")
module.DATA = data


class Process:
    def __init__(self, owner, argv):
        self.owner, self.args = owner, argv
        self.pid = 900000 + len(owner.processes)
        self.returncode, self.polls, self.waits = None, 0, 0
        self.environment = dict(os.environ)
        owner.processes.append(self)

    def poll(self):
        self.polls += 1
        if self.args[0] == "awesome" and self.polls > 4:
            self.returncode = self.owner.wm_code
        if self.args[0] == self.owner.dead:
            self.returncode = 3
        return self.returncode

    def wait(self, timeout):
        self.waits += 1
        if self.owner.stubborn and self.waits == 1:
            raise subprocess.TimeoutExpired(self.args, timeout)
        return 0


class World:
    def __init__(self):
        self.processes, self.calls, self.kills, self.handlers = [], [], [], {}
        self.foreign = self.existing_wm = self.stubborn = False
        self.secret = True
        self.agent = self.no_agent = self.no_secret = False
        self.bad_bus = self.bad_readiness = self.bad_config = False
        self.fail = self.dead = self.duplicate = self.interrupt = None
        self.wm_code = 0

    def run(self, argv, **kwargs):
        self.calls.append(argv)
        name = argv[0]
        assert kwargs["timeout"] == (1 if name in ("wmctrl", "awesome-client") and self.processes else 20)
        if name == self.fail:
            raise OSError("synthetic command failure")
        code, output = 0, ""
        if name == "wmctrl":
            if not self.processes:
                code = 0 if self.existing_wm else 1
            else:
                wm = self.processes[0]
                pid = wm.pid + 1 if self.bad_readiness else wm.pid
                output = "Name: awesome\nClass: N/A\nPID: {}\n".format(pid)
        elif name == "awesome-client":
            assert argv == [name, "return wm_ready == true"]
            output = "boolean false" if self.bad_config else "boolean true"
        elif name == "pgrep":
            assert argv[1:4] == ["-u", str(os.getuid()), "-x"]
            code = 0 if argv[-1] == self.duplicate else 1
        elif name == "gdbus":
            bus = argv[-1]
            assert bus in ("org.freedesktop.secrets", "org.awesomewm.awful", "org.freedesktop.Notifications", "org.kde.StatusNotifierWatcher")
            executable = "dunst" if bus == "org.freedesktop.Notifications" else "snixembed"
            owned = self.secret if bus == "org.freedesktop.secrets" else (
                self.foreign or any(p.args[0] == executable for p in self.processes))
            output = "invalid" if self.bad_bus else ("(true,)" if owned else "(false,)")
        elif name == "systemctl":
            assert argv in ([name, "--user", "start", "gnome-keyring-daemon.socket"],
                            [name, "--user", "start", "gcr-ssh-agent.socket"])
            if argv[-1] == "gcr-ssh-agent.socket":
                self.agent = not self.no_agent
        elif name == "gnome-keyring-daemon":
            assert argv == [name, "--start", "--components=secrets"]
            self.secret = not self.no_secret
        elif name == "xsetroot":
            assert argv == [name, "-solid", "#f6f5f4"]
        elif name == "xset":
            assert argv == [name, "s", "600", "600"]
        else:
            raise AssertionError(("unmocked command", argv))
        return types.SimpleNamespace(returncode=code, stdout=output)

    def popen(self, argv, **kwargs):
        assert kwargs == dict(stdin=subprocess.DEVNULL, stdout=kwargs["stdout"],
                              stderr=subprocess.STDOUT, start_new_session=True)
        if argv[0] == self.fail:
            raise OSError("synthetic spawn failure")
        return Process(self, argv)

    def kill(self, pid, sig):
        assert pid in [p.pid for p in self.processes], "foreign process killed"
        self.kills.append((pid, sig))

    def sleep(self, seconds):
        if self.interrupt is not None:
            self.handlers[self.interrupt](self.interrupt, None)

    def signal(self, sig, handler):
        previous = self.handlers.get(sig, signal.SIG_DFL)
        self.handlers[sig] = handler
        return previous


original = (subprocess.run, subprocess.Popen, os.killpg, signal.signal, module.time, Path.is_socket)
environment = dict(os.environ)
serial = 0


def exercise(world, failure=False, setup=None, inherited=True):
    global serial
    serial += 1
    folder = temporary / ("awesome-session-" + str(serial))
    folder.mkdir(mode=0o700)
    runtime = folder / "runtime"
    runtime.mkdir(mode=0o700)
    os.environ.clear()
    os.environ.update(HOME=str(folder), XDG_RUNTIME_DIR=str(runtime),
                      XDG_CACHE_HOME=str(folder / "cache"), DISPLAY=":synthetic",
                      XDG_SESSION_TYPE="x11", DBUS_SESSION_BUS_ADDRESS="mock:bus")
    if inherited:
        os.environ["SSH_AUTH_SOCK"] = "/synthetic/foreign-agent"
    subprocess.run, subprocess.Popen = world.run, world.popen
    os.killpg, signal.signal = world.kill, world.signal
    module.time = types.SimpleNamespace(sleep=world.sleep)
    Path.is_socket = lambda path: world.agent and path == runtime / "gcr/ssh"
    cleanup = setup(folder, runtime) if setup else None
    try:
        try:
            module.run()
            assert not failure, "expected failure"
        except (RuntimeError, OSError, KeyError, subprocess.SubprocessError):
            assert failure, "unexpected failure"
        assert {p.pid for p in world.processes} == {pid for pid, sig in world.kills}
        assert all(handler == signal.SIG_DFL for handler in world.handlers.values())
    finally:
        if cleanup:
            cleanup()
    return folder


try:
    world = World()
    folder = exercise(world)
    assert [p.args[0] for p in world.processes] == ["awesome", "dunst", "lxqt-policykit-agent", "snixembed", "nm-applet", "copyq", "xss-lock"]
    assert world.processes[0].args == ["awesome", "-c", str(data / "awesome/rc.lua")]
    assert world.processes[-1].args == ["xss-lock", "--transfer-sleep-lock", "--", "i3lock", "--nofork"]
    assert all(p.environment["SSH_AUTH_SOCK"] == "/synthetic/foreign-agent" for p in world.processes)
    assert not any(c[0] == "systemctl" for c in world.calls)
    forbidden = {"picom", "dwm", "dwmblocks", "wm-status", "wm-displays", "wm-keyboard", "setxkbmap", "xprop", "cbatticon", "pasystray"}
    assert not forbidden.intersection(c[0] for c in world.calls + [p.args for p in world.processes])
    assert [pid for pid, sig in world.kills] == [p.pid for p in reversed(world.processes)]
    assert (folder / "cache/wm").stat().st_mode & 0o777 == 0o700
    logfile = next((folder / "cache/wm").glob("*.log"))
    assert logfile.stat().st_mode & 0o777 == 0o600

    for attr, value in (("foreign", True), ("existing_wm", True), ("bad_bus", True),
                        ("duplicate", "copyq"), ("bad_readiness", True), ("bad_config", True), ("wm_code", 2)):
        world = World()
        setattr(world, attr, value)
        exercise(world, failure=True)
    for name in ("awesome", "dunst", "lxqt-policykit-agent", "snixembed", "nm-applet", "copyq", "xss-lock", "xset"):
        world = World()
        world.fail = name
        exercise(world, failure=True)
    for name in ("awesome", "dunst", "lxqt-policykit-agent", "snixembed", "xss-lock"):
        world = World()
        world.dead = name
        exercise(world, failure=True)
    for name in ("nm-applet", "copyq"):
        world = World()
        world.dead = name
        exercise(world)
    world = World()
    world.stubborn = True
    exercise(world)
    assert sum(sig == signal.SIGKILL for pid, sig in world.kills) == len(world.processes)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        world = World()
        world.interrupt = sig
        exercise(world)
    world = World()
    world.secret = False
    exercise(world, inherited=False)
    assert world.agent and world.secret
    assert all(p.environment["SSH_AUTH_SOCK"].endswith("/gcr/ssh") for p in world.processes)
    for attribute in ("no_agent", "no_secret"):
        world = World()
        world.secret = False
        setattr(world, attribute, True)
        exercise(world, failure=True, inherited=False)
        assert not world.processes
    for name in ("DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"):
        world = World()
        exercise(world, failure=True, setup=lambda folder, runtime, name=name: os.environ.pop(name) and None)
        assert not world.processes

    def locked(folder, runtime):
        key = hashlib.sha256(b":synthetic").hexdigest()[:16]
        directory = runtime / ("wm-" + key)
        directory.mkdir(mode=0o700)
        lock = (directory / "session.lock").open("w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock.close

    world = World()
    exercise(world, failure=True, setup=locked)
    assert not world.processes

    def linked(folder, runtime):
        target = folder / "untouched"
        target.mkdir()
        (folder / "cache").symlink_to(target, target_is_directory=True)
        return lambda: None

    world = World()
    folder = exercise(world, failure=True, setup=linked)
    assert not list((folder / "untouched").iterdir()) and not world.processes

    def linked_log(folder, runtime):
        cache = folder / "cache/wm"
        cache.mkdir(mode=0o700, parents=True)
        target = folder / "sentinel"
        target.write_text("unchanged")
        key = hashlib.sha256(b":synthetic").hexdigest()[:16]
        (cache / ("awesome-session-" + key + ".log")).symlink_to(target)

    world = World()
    folder = exercise(world, failure=True, setup=linked_log)
    assert (folder / "sentinel").read_text() == "unchanged" and not world.processes
    world = World()
    exercise(world, failure=True, setup=lambda folder, runtime: runtime.chmod(0o755))
    assert not world.processes
finally:
    subprocess.run, subprocess.Popen, os.killpg, signal.signal, module.time, Path.is_socket = original
    os.environ.clear()
    os.environ.update(environment)

# Wrapper executes only a generated inert supervisor, never the actual program.
fixture = temporary / "awesome-wrapper"
fixture.mkdir()
wrapper = fixture / "awesome-session"
wrapper.write_bytes((root / "session/awesome-session").read_bytes())
helper = fixture / "awesome-supervisor"
helper.write_text("#!/bin/sh\nprintf '%s\\n' \"$XDG_CURRENT_DESKTOP\" \"$XDG_SESSION_DESKTOP\" \"$DESKTOP_SESSION\" \"$GTK_THEME\" \"${KDE_FULL_SESSION-unset}\" \"${QT_QUICK_CONTROLS_CONF-unset}\" \"$1\"\n")
helper.chmod(0o700)
result = subprocess.run(["/bin/sh", str(wrapper), "argument with spaces"],
                        env={"PATH": "/usr/bin:/bin", "HOME": str(temporary),
                             "KDE_FULL_SESSION": "true", "QT_QUICK_CONTROLS_CONF": "foreign"},
                        text=True, capture_output=True, check=True, timeout=5)
assert result.stdout.splitlines() == ["awesome", "awesome", "awesome", "Adwaita", "unset", "unset", "argument with spaces"]
print("PASS: Awesome session isolation, readiness, failures, locks, agents and own cleanup")
