"""Launch/notification logic with inert processes; never start desktop/audio tools."""
import errno
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

print("PASS: startup failures, slow apps left alive, safe notifications and fallback (all tools mocked)")
