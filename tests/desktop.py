"""Launcher delegation/compatibility with forbidden-by-default process boundaries."""
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from unittest.mock import patch

root, temporary = map(Path, sys.argv[1:])
sys.path.insert(0, str(root / "scripts"))
launcher = types.ModuleType("launcher")
launcher.__file__ = str(root / "scripts/wm-launcher")
exec(compile(Path(launcher.__file__).read_text(), launcher.__file__, "exec"), launcher.__dict__)
notices = []
original_report = launcher.report
launcher.report = lambda name, message: notices.append((name, message))
cache = temporary / "old-cache"
cache.mkdir()
index = cache / "files.json"
index.write_text('{"paths":["old-file"]}')

with patch.object(subprocess, "run", side_effect=AssertionError("UNMOCKED PROCESS")), \
     patch.object(subprocess, "Popen", side_effect=AssertionError("UNMOCKED PROCESS")):
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="dwm"):
        for output, code in (("hostile command\n", 0), ("-1\n", 0), ("999\n", 0), ("0\n", 1)):
            with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], code, output)):
                assert launcher.choose({"legitimate": None}, "test", "2") is None
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "0\n")) as run:
            assert launcher.choose({"legitimate": None}, "test", "2") == "legitimate"
            argv = run.call_args.args[0]
            assert argv[argv.index("-monitor") + 1] == "-5" and "-no-custom" in argv
        assert launcher.actions()["Ayuda de atajos"] == (["wm-launcher", "--shortcuts"], False)
        assert launcher.actions()["Fondo de pantalla"] == (["wm-wallpaper"], False)
        with patch.object(subprocess, "Popen") as popen:
            launcher.execute_action("Fondo de pantalla")
            assert popen.call_args.args[0] == ["wm-run", "--", "wm-wallpaper"]
        with patch.object(launcher, "choose", return_value="Super+H — etiqueta; no ejecutar") as menu, \
             patch.object(sys, "argv", ["wm-launcher", "--shortcuts"]):
            launcher.run()
            items, prompt, monitor = menu.call_args.args
            assert prompt == "Atajos" and monitor is None
            for key in ("Super+F1", "Super+H", "Super+T", "Alt+Tab", "Super+L"):
                assert any(key in item for item in items), key
        with patch.object(Path, "home", side_effect=AssertionError("HOME traversal")), \
             patch.object(os, "walk", side_effect=AssertionError("file indexing")), \
             patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run, \
             patch.object(sys, "argv", ["wm-launcher"]):
            launcher.run()
            argv = run.call_args.args[0]
            assert "drun,window,Acciones" in argv and "-show-icons" in argv
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 2)), \
             patch.object(sys, "argv", ["wm-launcher"]):
            try:
                launcher.run()
                raise AssertionError("Rofi failure ignored")
            except RuntimeError:
                pass
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run, \
             patch.object(sys, "argv", ["wm-launcher", "--start"]):
            launcher.run()
            argv = run.call_args.args[0]
            assert "drun,window,Acciones" in argv
            theme = argv[argv.index("-theme-str") + 1]
            assert "location: southwest" in theme and "anchor: southwest" in theme
        def invalid_selection(argv, **kwargs):
            launcher.write_private(Path(kwargs["env"]["WM_ROFI_ACTION_FILE"]), "unknown; touch /synthetic\n")
            return subprocess.CompletedProcess(argv, 0)
        with patch.object(subprocess, "run", side_effect=invalid_selection), \
             patch.object(sys, "argv", ["wm-launcher", "--start"]):
            try:
                launcher.run()
                raise AssertionError("unlisted Rofi action accepted")
            except ValueError:
                pass
        config = temporary / "menu-config"
        menu_path = config / "wm/dwm/menu.json"
        menu_path.parent.mkdir(parents=True)
        extra_argv = ["synthetic-app", "a b", "; $(touch /synthetic)"]
        with patch.dict(os.environ, XDG_CONFIG_HOME=str(config)):
            menu_path.write_text(json.dumps({"Mi acción": {"argv": extra_argv}}))
            assert launcher.actions()["Mi acción"] == (extra_argv, False)
            with patch.object(subprocess, "Popen") as popen:
                launcher.execute_action("Mi acción")
                assert popen.call_args.args[0] == ["wm-run", "--", *extra_argv]
                assert not popen.call_args.kwargs.get("shell")
            menu_path.write_text(json.dumps({"Mi acción": {"argv": extra_argv, "confirm": True}}))
            with patch.object(launcher, "choose", return_value=None):
                launcher.execute_action("Mi acción")
            with patch.object(launcher, "choose", return_value="Confirmar"), \
                 patch.object(subprocess, "Popen") as popen:
                launcher.execute_action("Mi acción")
                assert popen.call_args.args[0] == ["wm-run", "--", *extra_argv]
            invalid = [[], {"Apagar": {"argv": ["fake"]}}, {"bad\nlabel": {"argv": ["x"]}},
                       {" spaced ": {"argv": ["x"]}}, {"-option": {"argv": ["x"]}},
                       {"bad": {"argv": "shell"}}, {"bad": {"argv": []}},
                       {"bad": {"argv": ["x", 1]}}, {"bad": {"argv": ["x\u0000"]}},
                       {"bad": {"argv": ["x"], "confirm": "true"}},
                       {"bad": {"argv": ["x"], "shell": True}}]
            for data in invalid:
                menu_path.write_text(json.dumps(data))
                try:
                    launcher.actions()
                    raise AssertionError("invalid menu configuration accepted: " + repr(data))
                except ValueError:
                    pass
            for content in ("{", " " * 65537):
                menu_path.write_text(content)
                try:
                    launcher.actions()
                    raise AssertionError("invalid/oversize JSON accepted")
                except ValueError:
                    pass
            with patch.dict(os.environ, XDG_CURRENT_DESKTOP="awesome"):
                assert "Ayuda de atajos" not in launcher.actions()
            menu_path.unlink()
            assert "Mi acción" not in launcher.actions()
        with patch.object(launcher, "choose", return_value=None):
            launcher.execute_action("Apagar")
        with patch.object(launcher, "choose", return_value="Confirmar"), patch.object(subprocess, "Popen") as popen:
            launcher.execute_action("Apagar", "2")
            assert popen.call_args.args[0] == ["wm-run", "--", "systemctl", "poweroff"]
        with patch.dict(os.environ, XDG_SESSION_ID=""):
            launcher.execute_action("Cerrar sesión")
            assert notices[-1][0] == "Cerrar sesión"
    with patch.dict(os.environ, XDG_CURRENT_DESKTOP="awesome"), \
         patch.object(launcher, "choose", side_effect=AssertionError("duplicate external UI")):
        assert "Fondo de pantalla" not in launcher.actions()
        for name in launcher.actions():
            with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "boolean true")) as run:
                launcher.execute_action(name)
                assert run.call_args.args[0] == ["awesome-client", 'return wm_launcher_action("{}")'.format(name)]
        for code, text in ((1, ""), (0, "boolean false")):
            count = len(notices)
            with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], code, text)):
                launcher.execute_action("Apagar")
            assert len(notices) == count + 1
        try:
            launcher.execute_action("hostile; expression")
            raise AssertionError("unlisted action accepted")
        except KeyError:
            pass
    with patch.object(subprocess, "run") as run:
        original_report("app", "synthetic error")
        assert run.call_args.args[0] == ["wm-run", "--error", "app", "synthetic error"]
assert index.read_text() == '{"paths":["old-file"]}'
assert (root / "session/dwm-xdg-terminals.list").read_text().splitlines() == ["Alacritty.desktop", "wm-st.desktop"]
print("PASS: Rofi delegation, no file indexing, safe selection, confirmations, native Awesome compatibility and errors")

# Wallpaper files are synthetic bytes; never decode the user's image or run X/GTK.
wallpaper = types.ModuleType("wallpaper")
wallpaper.__file__ = str(root / "scripts/wm-wallpaper")
exec(compile(Path(wallpaper.__file__).read_text(), wallpaper.__file__, "exec"), wallpaper.__dict__)
assets = temporary / "wallpaper-assets"
assets.mkdir()
(assets / "wallpaper.png").write_bytes(b"image:default")
datahome = temporary / "wallpaper-data"
saved = datahome / "wm/dwm/wallpaper"
source = temporary / "wallpaper ; $(command) ' spaces.png"
source.write_bytes(b"image:chosen")
applied = []


def fake_feh(argv, **kwargs):
    assert kwargs == {"check": True, "capture_output": True, "timeout": 20}
    if argv == ["xsetroot", "-solid", "#f6f5f4"]:
        applied.append((None, b"solid"))
        return subprocess.CompletedProcess(argv, 0)
    assert argv[:4] == ["feh", "--no-fehbg", "--bg-fill", "--"]
    assert Path(argv[4]).is_absolute() and len(argv) == 5
    content = Path(argv[4]).read_bytes()
    applied.append((Path(argv[4]), content))
    if not content.startswith(b"image:"):
        raise subprocess.CalledProcessError(1, argv, stderr=b"invalid image")
    return subprocess.CompletedProcess(argv, 0)


with patch.object(wallpaper, "DATA", assets), \
     patch.dict(os.environ, XDG_DATA_HOME=str(datahome)), \
     patch.object(subprocess, "Popen", side_effect=AssertionError("UNMOCKED PROCESS")), \
     patch.object(subprocess, "run", side_effect=AssertionError("UNMOCKED PROCESS")):
    # Cancel does not create private data or change an existing selection.
    with patch.object(sys, "argv", ["wm-wallpaper"]), \
         patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "")) as picker:
        wallpaper.run()
        assert picker.call_args.args[0][:2] == ["zenity", "--file-selection"]
        assert not datahome.exists()
    with patch.object(sys, "argv", ["wm-wallpaper"]), \
         patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 2, "")):
        try:
            wallpaper.run()
            raise AssertionError("picker error hidden")
        except RuntimeError:
            pass
    with patch.object(sys, "argv", ["wm-wallpaper"]), \
         patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, str(source) + "\n")), \
         patch.object(wallpaper, "set_wallpaper") as setter:
        wallpaper.run()
        setter.assert_called_once_with(str(source))
    with patch.object(subprocess, "run", side_effect=fake_feh), \
         patch.object(sys, "argv", ["wm-wallpaper", "--restore"]):
        default = assets / "wallpaper.png"
        default.unlink()
        wallpaper.run()
        assert applied[-1] == (None, b"solid") and not saved.exists()
        with patch.object(wallpaper.os, "replace", side_effect=OSError("synthetic disk failure")):
            try:
                wallpaper.set_wallpaper(source)
                raise AssertionError("first image publication failure hidden")
            except OSError:
                pass
        assert applied[-1] == (None, b"solid") and not saved.exists()
        assert not list(saved.parent.glob("wallpaper-*"))
        default.symlink_to(assets / "missing-image")
        try:
            wallpaper.run()
            raise AssertionError("dangling default symlink treated as absent")
        except OSError:
            pass
        default.unlink()
        wallpaper.set_wallpaper(source)
        wallpaper.run()
        assert applied[-1] == (saved, source.read_bytes())
        saved.unlink()
        default.write_bytes(b"image:default")
        wallpaper.run()
        assert applied[-1][1] == b"image:default" and not saved.exists()
        wallpaper.set_wallpaper(source)
        assert saved.read_bytes() == b"image:chosen" and source.read_bytes() == saved.read_bytes()
        assert saved.stat().st_mode & 0o777 == 0o600
        assert saved.parent.stat().st_mode & 0o777 == 0o700
        assert not list(saved.parent.glob("wallpaper-*"))
        source.unlink()
        (assets / "wallpaper.png").write_bytes(b"image:updated-default")
        wallpaper.run()
        assert applied[-1] == (saved, b"image:chosen")
        source.write_bytes(b"bad:not an image")
        try:
            wallpaper.set_wallpaper(source)
            raise AssertionError("bad image persisted")
        except subprocess.CalledProcessError:
            pass
        assert saved.read_bytes() == b"image:chosen" and applied[-1][0] == saved
        source.write_bytes(b"image:new")
        # Source symlinks are resolved; managed destination symlinks are rejected.
        link = temporary / "wallpaper-source-link"
        link.symlink_to(source)
        wallpaper.set_wallpaper(link)
        assert saved.read_bytes() == b"image:new"
        for failure in ("copy", "fsync", "replace", "timeout"):
            source.write_bytes(b"image:replacement")
            before = len(applied)
            target, name = {
                "copy": (wallpaper.shutil, "copyfileobj"),
                "fsync": (wallpaper.os, "fsync"),
                "replace": (wallpaper.os, "replace"),
                "timeout": (wallpaper, "apply"),
            }[failure]
            def failing_apply(path):
                if path != saved:
                    raise subprocess.TimeoutExpired("feh", 20)
                return real_apply(path)
            real_apply = wallpaper.apply
            effect = failing_apply if failure == "timeout" else OSError("synthetic disk failure")
            with patch.object(target, name, side_effect=effect):
                try:
                    wallpaper.set_wallpaper(source)
                    raise AssertionError("wallpaper failure hidden: " + failure)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            assert saved.read_bytes() == b"image:new"
            assert not list(saved.parent.glob("wallpaper-*"))
            if failure in ("replace", "timeout"):
                assert applied[-1] == (saved, b"image:new")
            else:
                assert len(applied) == before
        with patch.object(subprocess, "run", side_effect=FileNotFoundError("missing feh")):
            try:
                wallpaper.set_wallpaper(source)
                raise AssertionError("double apply/rollback failure hidden")
            except RuntimeError as error:
                assert "restauración" in str(error)
        assert saved.read_bytes() == b"image:new"
        for special in (temporary / "empty-wallpaper", temporary / "fifo-wallpaper"):
            if special.name.startswith("empty"):
                special.touch()
            else:
                os.mkfifo(special)
            try:
                wallpaper.set_wallpaper(special)
                raise AssertionError("invalid source accepted")
            except ValueError:
                pass
        assert not list(saved.parent.glob("wallpaper-*"))
        sentinel = temporary / "wallpaper-sentinel"
        sentinel.write_bytes(b"do not change")
        saved.unlink()
        saved.symlink_to(sentinel)
        try:
            wallpaper.run()
            raise AssertionError("saved symlink accepted")
        except OSError:
            pass
        assert sentinel.read_bytes() == b"do not change"
        saved.unlink()
        saved.write_bytes(b"image:private")
        saved.chmod(0o644)
        try:
            wallpaper.set_wallpaper(source)
            raise AssertionError("nonprivate saved image accepted")
        except ValueError:
            pass
        saved.chmod(0o600)
        os.link(saved, temporary / "wallpaper-hardlink")
        try:
            wallpaper.run()
            raise AssertionError("saved hardlink accepted")
        except ValueError:
            pass
        (temporary / "wallpaper-hardlink").unlink()
        lock = saved.parent / "wallpaper.lock"
        lock.unlink()
        lock.symlink_to(sentinel)
        try:
            wallpaper.run()
            raise AssertionError("lock symlink accepted")
        except OSError:
            pass
        lock.unlink()
        data_link = temporary / "wallpaper-directory-link"
        data_link.symlink_to(datahome, target_is_directory=True)
        with patch.dict(os.environ, XDG_DATA_HOME=str(data_link)):
            wallpaper.run()
            assert applied[-1] == (saved, b"image:private")
            wallpaper.set_wallpaper(source)
            assert saved.read_bytes() == source.read_bytes()
            wallpaper.run()
            assert applied[-1] == (saved, source.read_bytes())
        # Default HOME layout may have an ancestor symlink, not just the base.
        home = temporary / "wallpaper-home"
        home.mkdir()
        local = temporary / "wallpaper-local"
        local.mkdir()
        (home / ".local").symlink_to(local, target_is_directory=True)
        with patch.dict(os.environ, HOME=str(home), XDG_DATA_HOME=""):
            wallpaper.run()
            assert applied[-1][1] == b"image:updated-default"
            wallpaper.set_wallpaper(source)
            fallback_saved = local / "share/wm/dwm/wallpaper"
            assert fallback_saved.read_bytes() == source.read_bytes()
            wallpaper.run()
            assert applied[-1] == (fallback_saved, source.read_bytes())
        # Resolving the base must not resolve links in our managed directories.
        for relative in ("wm", "wm/dwm"):
            base = temporary / ("wallpaper-managed-" + relative.replace("/", "-"))
            managed = base / relative
            managed.parent.mkdir(parents=True)
            managed.symlink_to(saved.parent, target_is_directory=True)
            before = len(applied)
            with patch.dict(os.environ, XDG_DATA_HOME=str(base)):
                try:
                    wallpaper.run()
                    raise AssertionError("managed directory symlink accepted")
                except ValueError:
                    pass
            assert len(applied) == before
        saved.parent.chmod(0o755)
        with patch.dict(os.environ, XDG_DATA_HOME=str(data_link)):
            try:
                wallpaper.run()
                raise AssertionError("nonprivate directory accepted through base link")
            except ValueError:
                pass
        saved.parent.chmod(0o700)
        cycle = temporary / "wallpaper-cycle"
        cycle.symlink_to(cycle)
        for base in (cycle, sentinel):
            before = len(applied)
            with patch.dict(os.environ, XDG_DATA_HOME=str(base)):
                try:
                    wallpaper.run()
                    raise AssertionError("invalid data base accepted")
                except (OSError, ValueError, RuntimeError):
                    pass
            assert len(applied) == before
        assert sentinel.read_bytes() == b"do not change"
print("PASS: wallpaper picker/cancel, common fill argv, private atomic persistence, linked data base/HOME, default, rollback and hostile paths (synthetic files/X/GTK only)")
