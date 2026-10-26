"""Session integration with synthetic data only; every process call is forbidden by default."""
from contextlib import redirect_stderr, redirect_stdout
import configparser
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from unittest.mock import patch

root, temporary = map(Path, sys.argv[1:])
picom = (root / "session/picom.conf").read_text()
assert "shadow = false;" in picom
assert 'blur-method = "none";' in picom
assert "blur-background = false;" in picom
assert "blur-background-frame = false;" in picom


def check_notification_click(text):
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(text)
    assert config["global"]["mouse_left_click"] == "do_action, close_current"


check_notification_click((root / "session/dunstrc").read_text())
sys.path.insert(0, str(root / "scripts"))
import wm_session as shared

with patch.object(subprocess, "run", side_effect=AssertionError("UNMOCKED PROCESS")), \
     patch.object(subprocess, "Popen", side_effect=AssertionError("UNMOCKED PROCESS")):
    profiles, default = shared.themes(root / "awesome/config/themes.json")
    assert default == "bluebird" and list(profiles) == ["actual", "menta", "bluebird"]
    assert profiles[default]["panel_bg"] == "#212936"
    with patch.object(Path, "is_file", return_value=False):
        assert shared.resources(profiles[default]) == ("Adwaita", "Adwaita")
        assert shared.resources(profiles["menta"]) is None
    with patch.object(Path, "is_file", autospec=True, side_effect=lambda path: "gtk-3.0" in str(path)):
        assert shared.resources(profiles[default]) == ("Bluebird", "Adwaita")
    with patch.object(Path, "is_file", return_value=True):
        assert shared.resources(profiles[default]) == ("Bluebird", "elementary-xfce-dark")
    invalid = temporary / "invalid-themes.json"
    broken = json.loads((root / "awesome/config/themes.json").read_text())
    broken["default"] = "menta"
    invalid.write_text(json.dumps(broken))
    try:
        shared.themes(invalid)
        raise AssertionError("required-resource default accepted")
    except ValueError:
        pass
    private = temporary / "private"
    path = private / "state"
    assert shared.read_private(path) is None and not private.exists()
    shared.write_private(path, "bluebird\n")
    assert shared.read_private(path) == "bluebird\n" and path.stat().st_mode & 0o777 == 0o600
    path.unlink()
    sentinel = temporary / "sentinel"
    sentinel.write_text("untouched")
    path.symlink_to(sentinel)
    try:
        shared.write_private(path, "bad")
        raise AssertionError("symlink accepted")
    except OSError:
        pass
    assert sentinel.read_text() == "untouched"
    path.unlink()
    os.link(sentinel, path)
    try:
        shared.write_private(path, "bad")
        raise AssertionError("hard link accepted")
    except ValueError:
        pass
    assert sentinel.read_text() == "untouched"
    for output, code, expected in (("0\n", 0, "bad\nlabel"), ("1\n", 0, "second"),
                                   ("-1\n", 0, None), ("99\n", 0, None),
                                   ("arbitrary", 0, None), ("0\n", 1, None)):
        def menu(argv, **kwargs):
            assert argv[:2] == ["rofi", "-no-config"]
            assert argv[argv.index("-monitor") + 1] == "-5"
            assert "-no-custom" in argv and "-format" in argv
            assert kwargs["input"] == "bad label\nsecond\n"
            return subprocess.CompletedProcess(argv, code, output, "")
        with patch.object(subprocess, "run", side_effect=menu):
            assert shared.choose(["bad\nlabel", "second"], "Synthetic") == expected

# Health is bounded, private, current, scoped to this session, and data only.
health_directory = temporary / "health-data"
health_directory.mkdir(mode=0o700)
health_path = health_directory / "health.json"
shared.write_private(health_directory / "session.id", "synthetic")
valid_health = {"session": "synthetic", "issues": {"dunst": "No disponible"}, "updated": 10}
with patch.dict(os.environ, WM_DWM_RUNTIME=str(health_directory), XDG_SESSION_ID="synthetic"), \
     patch.object(shared.time, "monotonic", return_value=11):
    shared.write_private(health_path, json.dumps(valid_health))
    assert shared.session_health() == {"dunst": "No disponible"}
    invalid_health = [[], {}, dict(valid_health, session="foreign"), dict(valid_health, issues=[]),
                     dict(valid_health, updated=True), dict(valid_health, updated=float("nan")),
                     dict(valid_health, updated=float("inf")), dict(valid_health, updated=12),
                     dict(valid_health, updated=-20), dict(valid_health, extra=True),
                     dict(valid_health, issues={"bad\nname": "x"}), dict(valid_health, issues={"dunst": "bad\ntext"}),
                     dict(valid_health, issues={"dunst": 1}), dict(valid_health, issues={"dunst": "x" * 161}),
                     dict(valid_health, issues={str(i): "x" for i in range(17)})]
    for data in invalid_health:
        shared.write_private(health_path, json.dumps(data))
        try:
            shared.session_health()
            raise AssertionError("invalid health accepted: " + repr(data))
        except (ValueError, RuntimeError):
            pass
    for content in ("{", " " * 4097):
        shared.write_private(health_path, content)
        try:
            shared.session_health()
            raise AssertionError("invalid/oversize health accepted")
        except ValueError:
            pass
    health_path.unlink()
    health_path.symlink_to(health_directory / "session.id")
    try:
        shared.session_health()
        raise AssertionError("linked health accepted")
    except OSError:
        pass
    health_path.unlink()
    shared.write_private(health_path, json.dumps(valid_health))
    shared.write_private(health_directory / "session.id", "another-session")
    try:
        shared.session_health()
        raise AssertionError("inactive health accepted")
    except RuntimeError:
        pass


def load(name):
    module = types.ModuleType(name)
    module.__file__ = str(root / "scripts" / name)
    exec(compile(Path(module.__file__).read_text(), module.__file__, "exec"), module.__dict__)
    return module


with patch.object(subprocess, "run", side_effect=AssertionError("UNMOCKED PROCESS")), \
     patch.object(subprocess, "Popen", side_effect=AssertionError("UNMOCKED PROCESS")):
    app = load("wm-appearance")
    app.DATA = temporary / "payload"
    app.DATA.mkdir()
    (app.DATA / "dunstrc").write_text((root / "session/dunstrc").read_text())
    directory = temporary / "appearance-runtime"
    saved = temporary / "saved-appearance" / "state"
    with patch.object(app, "themes", return_value=(profiles, default)), \
         patch.object(app, "resources", return_value=("Adwaita", "Adwaita")), \
         patch.object(app, "state_path", return_value=saved), \
         patch.object(sys, "argv", ["wm-appearance", "--prepare", str(directory)]):
        app.run()
        assert (directory / "theme").read_text() == "bluebird\n" and not saved.exists()
        check_notification_click((directory / "dunstrc").read_text())
        for profile in profiles.values():
            with patch.object(app, "resources", return_value=("Adwaita", "Adwaita")):
                check_notification_click(app.render(profile)["dunstrc"])
        assert (directory / "rofi.rasi").read_text() == (root / "session/rofi.rasi").read_text()
        for file in directory.iterdir():
            assert file.stat().st_mode & 0o777 == 0o600
        calls = []
        with patch.dict(os.environ, WM_DWM_XSETTINGSD_PID="5678"), \
             patch.object(app, "command", side_effect=lambda argv: calls.append(argv) or ""), \
             patch.object(os, "kill") as kill:
            app.apply(directory, profiles[default], profiles[default])
            assert saved.read_text() == "bluebird\n"
            check_notification_click((directory / "dunstrc").read_text())
            assert calls[0] == ["dunstctl", "reload", str(directory / "dunstrc")]
            assert calls[1][-1] == "#f7f7f7 #212936 #909090 #f5f5f5 #7e9ebd #7e9ebd"
            kill.assert_called_once()
        before = {file.name: file.read_bytes() for file in directory.iterdir()}
        failed = []
        def fail_publish(argv):
            if argv[0] == "xprop" and not failed:
                failed.append(True)
                raise subprocess.CalledProcessError(1, argv)
            return ""
        with patch.dict(os.environ, WM_DWM_XSETTINGSD_PID="5678"), \
             patch.object(app, "command", side_effect=fail_publish), patch.object(os, "kill"):
            try:
                app.apply(directory, profiles["actual"], profiles[default])
                raise AssertionError("theme failure accepted")
            except subprocess.CalledProcessError:
                pass
        assert before == {file.name: file.read_bytes() for file in directory.iterdir()}
        assert saved.read_text() == "bluebird\n"
        real_write = app.write_private
        rollback_calls, failure = [], []
        def rollback_command(argv):
            rollback_calls.append(argv)
            if argv[0] == "xprop" and not failure:
                failure.append(True)
                raise subprocess.CalledProcessError(1, argv)
            return ""
        def rollback_write(path, content):
            if path.name == "rofi.rasi" and content.encode() == before["rofi.rasi"]:
                raise OSError("synthetic rollback write denied")
            real_write(path, content)
        errors = io.StringIO()
        with patch.dict(os.environ, WM_DWM_XSETTINGSD_PID="5678"), \
             patch.object(app, "command", side_effect=rollback_command), patch.object(os, "kill"), \
             patch.object(app, "write_private", side_effect=rollback_write), redirect_stderr(errors):
            try:
                app.apply(directory, profiles["actual"], profiles[default])
                raise AssertionError("incomplete rollback hidden")
            except subprocess.CalledProcessError:
                pass
        assert "rollback incompleto" in errors.getvalue()
        assert len([argv for argv in rollback_calls if argv[0] == "xprop"]) == 2
        real_write(directory / "rofi.rasi", before["rofi.rasi"].decode())
        assert before == {file.name: file.read_bytes() for file in directory.iterdir()}
        def fail_state(path, content):
            if path == saved:
                raise OSError("synthetic state write denied")
            real_write(path, content)
        with patch.dict(os.environ, WM_DWM_XSETTINGSD_PID="5678"), \
             patch.object(app, "command", return_value=""), patch.object(os, "kill"), \
             patch.object(app, "write_private", side_effect=fail_state):
            try:
                app.apply(directory, profiles["actual"], profiles[default])
                raise AssertionError("persistence failure hidden")
            except RuntimeError as error:
                assert "Tema aplicado" in str(error)
        assert (directory / "theme").read_text() == "actual\n" and saved.read_text() == "bluebird\n"

    launcher = load("wm-launcher")
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm", ROFI_RETV="0"), \
         patch.object(sys, "argv", ["wm-launcher", "--rofi-actions"]):
        output = io.StringIO()
        with redirect_stdout(output):
            launcher.run()
        assert "\0no-custom\x1ftrue\n" in output.getvalue()
        assert all(name in output.getvalue() for name in launcher.actions())
    channel = temporary / "mode-channel" / "action"
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm", ROFI_RETV="1", WM_ROFI_ACTION_FILE=str(channel)), \
         patch.object(sys, "argv", ["wm-launcher", "--rofi-actions", "Apagar"]):
        launcher.run()
        assert shared.read_private(channel) == "Apagar\n"
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm", ROFI_RETV="2"), \
         patch.object(sys, "argv", ["wm-launcher", "--rofi-actions", "touch /synthetic"]):
        launcher.run()
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm"), \
         patch.object(launcher, "choose", return_value=None):
        launcher.execute_action("Apagar")  # No unmocked subprocess may be reached.
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm"), \
         patch.object(launcher, "choose", return_value="Confirmar"), \
         patch.object(subprocess, "Popen") as popen:
        launcher.execute_action("Apagar")
        assert popen.call_args.args[0] == ["wm-run", "--", "systemctl", "poweroff"]
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm", XDG_SESSION_ID="synthetic"), \
         patch.object(launcher, "choose", return_value="Confirmar"), \
         patch.object(subprocess, "Popen") as popen:
        launcher.execute_action("Cerrar sesión")
        assert popen.call_args.args[0] == ["wm-run", "--", "wm-supervisor", "--logout"]
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm", XDG_SESSION_ID="synthetic"), \
         patch.object(launcher, "choose", return_value="Cancelar"):
        launcher.execute_action("Cerrar sesión")
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm"), \
         patch.object(sys, "argv", ["wm-launcher"]), \
         patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
        launcher.run()
        argv = run.call_args.args[0]
        assert "drun,window,Acciones" in argv and "-terminal" in argv
    dispatched, closed = [], []
    status = 0
    def finish_rofi(argv, **kwargs):
        shared.write_private(Path(kwargs["env"]["WM_ROFI_ACTION_FILE"]), "Apagar\n")
        closed.append(True)
        return subprocess.CompletedProcess(argv, status)
    def dispatch(name, monitor):
        assert closed, "action dispatched before Rofi released the keyboard"
        dispatched.append(name)
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm"), patch.object(sys, "argv", ["wm-launcher"]), \
         patch.object(subprocess, "run", side_effect=finish_rofi), patch.object(launcher, "execute_action", side_effect=dispatch):
        launcher.run()
        assert dispatched == ["Apagar"]
        status = 1; dispatched.clear(); launcher.run()
        assert not dispatched, "cancelled Rofi dispatched a stale selection"
    cmd = load("wm-command")
    text = "printf '%s' 'x; $(touch /synthetic)'"
    replies = [subprocess.CompletedProcess([], 0, "printf\n"), subprocess.CompletedProcess([], 0, text + "\n")]
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm"), patch.object(sys, "argv", ["wm-command"]), \
         patch.object(subprocess, "run", side_effect=replies) as run, patch.object(subprocess, "Popen") as popen:
        cmd.run()
        assert run.call_args_list[1].args[0][0] == "rofi"
        assert popen.call_args.args[0] == ["alacritty", "-e", "/bin/sh", "-c", cmd.WRAPPER, "wm-command", text]
    notes = load("wm-notifications")
    data = {"type": "aa{sv}", "data": [[{"id": {"type": "i", "data": 42},
            "summary": {"type": "s", "data": "bad\n$(touch never)"}, "body": {"type": "s", "data": "text"}}]]}
    rows = notes.history(json.dumps(data))
    assert len(rows) == 1 and "\n" not in next(iter(rows))
    calls = []
    def notify(argv):
        calls.append(argv)
        return "0" if argv[1] == "get-pause-level" else json.dumps(data) if argv[1] == "history" else ""
    with patch.object(notes, "command", side_effect=notify), patch.object(notes, "choose", return_value=next(iter(rows))):
        notes.run()
        assert calls[-1] == ["dunstctl", "history-pop", "42"]
    with patch.object(notes, "command", side_effect=notify), patch.object(notes, "choose", return_value="No molestar: desactivado"):
        notes.run()
        assert calls[-1] == ["dunstctl", "set-pause-level", "50"]
    data["data"][0][0]["id"]["data"] = "42;touch never"
    try:
        notes.history(json.dumps(data))
        raise AssertionError("invalid notification ID accepted")
    except ValueError:
        pass
    try:
        notes.history("[]")
        raise AssertionError("invalid history container accepted")
    except ValueError:
        pass
    status = load("wm-status")
    with patch.object(status, "command", return_value="balanced") as command, patch.object(subprocess, "Popen") as popen:
        assert status.block("power", "1") == "PWR Equilibrado"
        assert command.call_args.args[0] == ["powerprofilesctl", "get"]
        assert popen.call_args.args[0] == ["wm-run", "--", "xfce4-power-manager-settings"]
    with patch.object(status, "command", side_effect=["4", "50"]), \
         patch.object(status, "session_health", return_value={}):
        assert status.block("notifications", "") == "Avisos 4 · DND"
    with patch.object(status, "command", side_effect=RuntimeError("Dunst unavailable")), \
         patch.object(status, "session_health", return_value={"dunst": "Deshabilitado", "picom": "Recuperando"}):
        assert status.block("notifications", "") == "Fallos 2 · Avisos ?"
    with patch.object(status, "command", side_effect=["0", "0"]), \
         patch.object(status, "session_health", side_effect=ValueError("invalid status")):
        assert status.block("notifications", "") == "Fallos ? · Avisos 0"
    assert not hasattr(status, "watch_power") and not hasattr(status, "automatic")

print("PASS: Bluebird/resources, atomic appearance and rollback, safe Rofi modes, terminal argv, Dunst history/quiet and read-only status")
