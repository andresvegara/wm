"""Real launcher functions with inert subprocesses, wrapper with a synthetic PTY."""
import errno
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import time
import types

root, temporary = map(Path, sys.argv[1:])
module = types.ModuleType("command")
module.__file__ = str(root / "scripts/wm-command")
source = Path(module.__file__).read_text()
exec(compile(source, module.__file__, "exec"), module.__dict__)
original_run, original_popen, original_argv = subprocess.run, subprocess.Popen, sys.argv
calls = []
selection, code, failure = "", 0, None


def run(argv, **kwargs):
    calls.append((argv, kwargs))
    if argv[0] == failure:
        raise subprocess.TimeoutExpired(argv, 10)
    if argv == ["dmenu_path"]:
        assert kwargs["timeout"] == 10 and kwargs["check"]
        return types.SimpleNamespace(stdout="echo\nprintf\n", returncode=0)
    assert argv == ["dmenu", "-c", "-i", "-l", "12", "-p", "Ejecutar", "-m", "2"]
    assert kwargs["input"] == "echo\nprintf\n"
    return types.SimpleNamespace(stdout=selection, returncode=code)


def popen(argv, **kwargs):
    calls.append((argv, kwargs))
    assert argv == ["alacritty", "-e", "/bin/sh", "-c", module.WRAPPER, "wm-command", selection.removesuffix("\n")]
    assert kwargs == {"start_new_session": True}
    if failure == "alacritty":
        raise OSError("synthetic spawn failure")
    return object()


try:
    subprocess.run, subprocess.Popen = run, popen
    sys.argv = ["wm-command", "-m", "2"]
    for selection, code in (("", 0), (" \t\n", 0), ("echo nope\n", 1)):
        calls.clear()
        assert module.run() == 0 and len(calls) == 2
    for selection in ("printf '%s' 'ñ 😀 $HOME'\n", 'echo "a b"; printf \'%s\' "$USER"\n', "  echo spaces  \n"):
        code = 0
        calls.clear()
        assert module.run() == 0 and len(calls) == 3
    for failure in ("dmenu_path", "dmenu", "alacritty"):
        try:
            module.run()
            raise AssertionError("missing failure")
        except (OSError, subprocess.SubprocessError):
            pass
finally:
    subprocess.run, subprocess.Popen, sys.argv = original_run, original_popen, original_argv

# No GUI, sudo, bus or audio: only a local shell with a temporary controlling TTY.
# setsid + TIOCSCTTY is not needed here: child stdin/out/err are a PTY, as Alacritty supplies.
for status in (0, 7):
    master, slave = pty.openpty()
    text = "test -t 0 && test -t 1 && test -t 2 || exit 99; printf 'TTY-ñ'; exit {}".format(status)
    process = original_popen(["/bin/sh", "-c", module.WRAPPER, "wm-command", text],
                             stdin=slave, stdout=slave, stderr=slave,
                             env={"PATH": "/usr/bin:/bin", "HOME": str(temporary), "LC_ALL": "C.UTF-8"})
    os.close(slave)
    output = b""
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    data = os.read(master, 4096)
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
                    break
                if not data:
                    break
                output += data
            if status and b"Pulsa Enter" in output:
                assert process.poll() is None, "error must wait for Enter"
                os.write(master, b"\n")
                break
            if process.poll() is not None:
                break
        assert process.wait(timeout=3) == status
        assert b"TTY-" in output
        assert (b"Pulsa Enter" in output) == bool(status)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
assert "history" not in source.lower() and "shell=True" not in source
print("PASS: Awesome command cancellation, argv, failures and synthetic TTY exit/pause")
