"""Launch/notification logic with inert processes; never start desktop/audio tools."""
import configparser
import errno
import os
from pathlib import Path
import subprocess
import sys
import types

root, temporary = map(Path, sys.argv[1:])


def load(name):
    module = types.ModuleType(name)
    module.__file__ = str(root / "scripts" / name)
    exec(compile(Path(module.__file__).read_text(), module.__file__, "exec"), module.__dict__)
    return module


runner = load("wm-run")
original_run, original_popen = subprocess.run, subprocess.Popen
calls = []
code = 0
notification_code = 0
slow = False
missing = False


def popen(argv, **kwargs):
    assert argv == ["synthetic", "with spaces", "$(never-run);secret=value"]
    assert kwargs == {}  # no pipes, shell, stream capture or redirection
    if missing:
        raise OSError(errno.ENOENT, "synthetic missing executable")
    return Process()


class Process:
    def wait(self, timeout):
        assert timeout == 1.5
        if slow:
            raise subprocess.TimeoutExpired("synthetic", timeout)
        return code


def notify(argv, **kwargs):
    assert "shell" not in kwargs and kwargs["timeout"] in (3, 17)
    assert argv[0] in ("notify-send", "xmessage")
    calls.append(argv)
    return types.SimpleNamespace(returncode=notification_code)


try:
    subprocess.Popen, subprocess.run = popen, notify
    args = ["synthetic", "with spaces", "$(never-run);secret=value"]
    assert runner.launch(args) == 0 and not calls
    slow = True
    assert runner.launch(args) == 0 and not calls  # live app is not killed
    slow = False
    code = 7
    assert runner.launch(args) == 7
    assert len(calls) == 1 and "código 7" in calls[0][-1]
    assert "secret=value" not in repr(calls)
    calls.clear()
    missing = True
    assert runner.launch(args) == 1
    assert "No se pudo ejecutar" in calls[-1][-1]
    missing = False
    calls.clear()
    notification_code = 1
    runner.report("<hostile>\napp", "synthetic <message>")
    assert calls[0][-2:] == ["No se pudo iniciar &lt;hostile&gt; app", "synthetic &lt;message&gt;"]
    assert calls[1][:4] == ["xmessage", "-center", "-timeout", "15"]
    subprocess.run = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("no notification tools"))
    runner.report("app", "still reports to stderr")
finally:
    subprocess.run, subprocess.Popen = original_run, original_popen

controller = load("wm-control")
assert controller.volume("Volume: 0.56\n")[:2] == (56, "56%")
assert controller.volume("Volume: 0.56 [MUTED]\n") == (0, "Silenciado (56%)", "audio-volume-muted")
assert controller.volume("Volume: 1.50")[0] == 100
assert controller.brightness("synthetic,backlight,420,42%,1000\n") == (42, "42%", "display-brightness")
for value in ("bad", "Volume: NaN", "Volume: -0.1", "Volume: inf", "Volume: " + "9" * 400):
    try:
        controller.volume(value)
        raise AssertionError("bad volume accepted")
    except RuntimeError:
        pass
for value in ("bad", "x,backlight,1,101%,10", "x,leds,1,10%,10", "x,backlight,11,10%,10",
              "x,backlight,1,10%,0", "x,backlight,1,10%,10\nx,backlight,1,10%,10"):
    try:
        controller.brightness(value)
        raise AssertionError("bad brightness accepted")
    except RuntimeError:
        pass

runtime = temporary / "control-runtime"
runtime.mkdir(mode=0o700)
old_runtime = os.environ.get("XDG_RUNTIME_DIR")
os.environ["XDG_RUNTIME_DIR"] = str(runtime)
commands = []
fail_command = None
bad_volume = False


def hardware(argv, **kwargs):
    assert "shell" not in kwargs
    commands.append(argv)
    if argv[0] == "wm-run":
        assert argv[1] == "--error" and kwargs["timeout"] == 20
        return types.SimpleNamespace(returncode=0)
    assert argv[0] in ("wpctl", "brightnessctl", "notify-send")
    assert kwargs["env"]["LC_ALL"] == "C" and kwargs["timeout"] == 5
    assert kwargs["stdout"] == subprocess.PIPE and kwargs["stderr"] == subprocess.DEVNULL
    if argv == fail_command:
        return types.SimpleNamespace(returncode=1, stdout="")
    output = ""
    if argv[:2] == ["wpctl", "get-volume"]:
        output = "invalid" if bad_volume else "Volume: 0.65 [MUTED]\n"
    if argv == ["brightnessctl", "--class=backlight", "--machine-readable", "info"]:
        output = "synthetic,backlight,42,42%,100\n"
    return types.SimpleNamespace(returncode=0, stdout=output)


try:
    subprocess.run = hardware
    for action, expected in controller.ACTIONS.items():
        commands.clear()
        controller.control(action)
        assert commands[0] == expected and len(commands) == 3
        assert commands[2][0] == "notify-send" and "--app-name=wm-osd" in commands[2]
        assert "--expire-time=1500" in commands[2]
        if action.startswith("brightness"):
            assert "--hint=int:value:42" in commands[2]
            assert "--hint=string:x-dunst-stack-tag:wm-brightness" in commands[2]
        else:
            assert "--hint=int:value:0" in commands[2] and commands[2][-1] == "Silenciado (65%)"
            assert "--hint=string:x-dunst-stack-tag:wm-volume" in commands[2]
    commands.clear()
    fail_command = controller.ACTIONS["volume-up"]
    try:
        controller.control("volume-up")
        raise AssertionError("failed action showed success")
    except RuntimeError:
        pass
    assert commands == [fail_command]
    fail_command = None
    bad_volume = True
    commands.clear()
    try:
        controller.control("volume-up")
        raise AssertionError("malformed state showed success")
    except RuntimeError:
        pass
    assert len(commands) == 2 and not any(argv[0] == "notify-send" for argv in commands)
    bad_volume = False
    fail_command = controller.ACTIONS["volume-up"]
    controller.sys.argv = ["wm-control", "volume-up"]
    assert controller.run() == 1 and commands[-1][:2] == ["wm-run", "--error"]
    fail_command = None
    lock = runtime / "wm-control-volume.lock"
    lock.unlink()
    sentinel = runtime / "sentinel"
    sentinel.write_text("untouched")
    lock.symlink_to(sentinel)
    commands.clear()
    try:
        controller.control("volume-up")
        raise AssertionError("symlink lock accepted")
    except OSError:
        pass
    assert not commands and sentinel.read_text() == "untouched"
finally:
    subprocess.run = original_run
    if old_runtime is None:
        os.environ.pop("XDG_RUNTIME_DIR", None)
    else:
        os.environ["XDG_RUNTIME_DIR"] = old_runtime

config = configparser.ConfigParser()
config.read(root / "session/dunstrc")
assert config["wm-osd"]["appname"] == "wm-osd"
assert config["wm-osd"]["timeout"] == "1500ms" and config["wm-osd"]["history_ignore"] == "yes"
print("PASS: launch failures/fallback, OSD controls, real-state parsing, errors and private locks (all tools mocked)")
