"""Display manager with synthetic RandR/autorandr/menu only; forks touch temp files."""
import copy
import os
from pathlib import Path
import signal
import subprocess
import sys
import types

root, temporary = map(Path, sys.argv[1:])
module = types.ModuleType("displays")
module.__file__ = str(root / "scripts/wm-displays")
exec(compile(Path(module.__file__).read_text(), module.__file__, "exec"), module.__dict__)
work = temporary / "displays"
work.mkdir(mode=0o700)


def screen(name="DP-1", enabled=True, x=0, y=0, rotation="normal", primary=True):
    return dict(name=name, enabled=enabled, x=x, y=y, rotation=rotation, primary=primary)


def verbose(screens):
    rows = ["Screen 0: minimum 8 x 8, current 3840 x 2160, maximum 32767 x 32767"]
    for index, value in enumerate(screens):
        geometry = " primary" if value["primary"] and value["enabled"] else ""
        if value["enabled"]:
            geometry += " 1920x1080+{}+{} (0x10) {}".format(value["x"], value["y"], value["rotation"])
        rows += [value["name"] + " connected" + geometry + " (normal left inverted right x axis y axis) 300mm x 200mm",
                 "\tEDID:", "\t\t" + ("{:02x}".format(index + 1) * 16),
                 "\tTransform: 1.000000 0.000000 0.000000",
                 "\t           0.000000 1.000000 0.000000",
                 "\t           0.000000 0.000000 1.000000", "\t           filter:"]
        for name, width, height, rates in (("1920x1080", 1920, 1080, ["60.00", "59.94"]),
                                           ("Cinema-wide", 1280, 720, ["50.00"])):
            for rate in rates:
                flags = " *current +preferred" if name == "1920x1080" and rate == "60.00" and value["enabled"] else ""
                rows += ["  {} (0x10) 148.500MHz +HSync +VSync{}".format(name, flags),
                         "        h: width {} start 2000 end 2050 total 2200 clock 67.50KHz".format(width),
                         "        v: height {} start 1100 end 1105 total 1125 clock {}Hz".format(height, rate)]
    rows.append("HDMI-9 disconnected (normal left inverted right x axis y axis)")
    return "\n".join(rows)


one = verbose([screen(x=-1920, y=-20)])
two = verbose([screen(), screen("HDMI-1", x=1920, primary=False)])
parsed = module.parse(one)
assert parsed["DP-1"]["supported"]
assert parsed["DP-1"]["x"] == -1920 and parsed["DP-1"]["y"] == -20
assert parsed["DP-1"]["rate"] == "60.00"
assert parsed["DP-1"]["modes"]["Cinema-wide"]["size"] == (1280, 720)
assert parsed["DP-1"]["modes"]["1920x1080"]["rates"] == ["60.00", "59.94"]
assert parsed["DP-1"]["edid"] == "01" * 16
assert module.parse(verbose([screen(rotation="left")]))["DP-1"]["rotation"] == "left"
assert module.parse(verbose([screen(enabled=False)]))["DP-1"]["mode"] == "1920x1080"
assert not module.parse(one.replace("Transform: 1.000000", "Transform: 2.000000"))["DP-1"]["supported"]
assert not module.parse(one.replace("normal (normal", "normal x axis (normal"))["DP-1"]["supported"]
assert module.identity(parsed) == module.identity(module.parse(verbose([screen(x=50, primary=False)])))
assert module.identity(parsed) != module.identity(module.parse(two))
assert module.identity(parsed) != module.identity(module.parse(one.replace("01" * 16, "02" * 16)))
for text in ("invalid", "DP-1 connected", one.replace("DP-1 connected", "-bad connected"),
             one.replace("Cinema-wide (", "--bad ("),
             one.replace("Cinema-wide (", "Cinema wide (")):
    try:
        module.parse(text)
        raise AssertionError("invalid RandR accepted")
    except RuntimeError:
        pass

assert module.parse(one.replace("HDMI-9 disconnected", "HDMI-9 unknown connection")) == parsed
assert not module.parse(one.replace("\tEDID:\n\t\t" + "01" * 16 + "\n", ""))["DP-1"]["edid"]

# Real graph/rotation/alignment code, including disabled references and cycles.
draft = module.parse(two)
draft["HDMI-1"]["mode"] = "Cinema-wide"
draft["HDMI-1"]["rate"] = "50.00"
for direction, alignment, position in (("right", 0, (1920, 0)), ("right", 1, (1920, 180)),
                                       ("right", 2, (1920, 360)), ("below", 1, (320, 1080)),
                                       ("left", 1, (0, 180)), ("above", 2, (640, 0))):
    draft["HDMI-1"]["relative"] = "DP-1", direction, alignment
    result = module.layout(draft)
    assert (result["HDMI-1"]["x"], result["HDMI-1"]["y"]) == position
    assert min(value["x"] for value in result.values()) == 0
    assert min(value["y"] for value in result.values()) == 0
    assert draft["DP-1"]["x"] == 0  # no mutation

draft["HDMI-1"]["rotation"] = "left"
draft["HDMI-1"]["relative"] = "DP-1", "right", 1
assert module.layout(draft)["HDMI-1"]["size"] == (720, 1280)
draft["HDMI-1"]["relative"] = "DP-1", "same", 0
result = module.layout(draft)
assert result["HDMI-1"]["size"] == (1920, 1080)
assert result["HDMI-1"]["mode"] == "1920x1080"
assert result["HDMI-1"]["x"] == result["DP-1"]["x"] == 0
invalid = copy.deepcopy(draft)
invalid["DP-1"]["relative"] = "HDMI-1", "right", 0
for bad in (invalid, {name: dict(value, enabled=False) for name, value in draft.items()},
            dict(draft, **{"DP-1": dict(draft["DP-1"], enabled=False)})):
    try:
        module.layout(bad)
        raise AssertionError("unsafe graph accepted")
    except RuntimeError:
        pass
invalid = copy.deepcopy(draft)
del invalid["HDMI-1"]["modes"]["1920x1080"]
try:
    module.layout(invalid)
    raise AssertionError("incompatible clone accepted")
except RuntimeError:
    pass
argv = module.arguments(draft)
assert argv[:3] == ["xrandr", "--output", "DP-1"]
assert argv.count("--primary") == 1 and "--noprimary" not in argv
assert isinstance(argv, list) and all(isinstance(arg, str) for arg in argv)


class World:
    def __init__(self):
        self.current = work / "current"
        self.current.write_text(one)
        self.events = work / "events"
        self.events.write_text("")
        self.fail_save = self.fail_apply = False

    def command(self, argv, env=None):
        with self.events.open("a") as log:
            log.write(repr(argv) + "\n")
        if argv == ["xrandr", "--verbose"]:
            assert env["LC_ALL"] == "C"
            return self.current.read_text()
        if argv[0] == "autorandr":
            assert argv[1] == "--ignore-lid"
            assert env["HOME"] != os.environ["HOME"]
            assert Path(env["XDG_CONFIG_DIRS"]).is_dir()
            assert env["XAUTHORITY"] == os.environ.get("XAUTHORITY", str(Path.home() / ".Xauthority"))
            profiles = Path(env["XDG_CONFIG_HOME"]) / "autorandr"
            if "--save" in argv:
                if self.fail_save and argv[argv.index("--save") + 1] != "rollback":
                    raise RuntimeError("synthetic save failure")
                version = profiles / argv[argv.index("--save") + 1]
                version.mkdir(mode=0o700, parents=True)
                (version / "config").write_text(self.current.read_text())
                (version / "setup").write_text("synthetic EDID")
            elif "--load" in argv:
                version = profiles / argv[argv.index("--load") + 1]
                self.current.write_text((version / "config").read_text())
            else:
                raise AssertionError(argv)
            return ""
        if argv[0] == "xrandr":
            if "--off" in argv:
                self.current.write_text(self.current.read_text().replace(
                    "HDMI-9 disconnected 1920x1080+0+0", "HDMI-9 disconnected"))
            elif "--auto" in argv:
                current = module.parse(self.current.read_text())
                self.current.write_text(verbose([screen(name, enabled=name == argv[2]) for name in current]))
            elif "--dryrun" not in argv:
                self.current.write_text(verbose([screen(x=100)]))
                if self.fail_apply:
                    raise RuntimeError("synthetic partial apply failure")
            return ""
        raise AssertionError(("unmocked command", argv))


world = World()
original_command = module.command
module.command = world.command
base = module.private(work / "profiles")
key = module.identity(module.state())
module.save(base, key)
old = module.profile(base, key)
old_target = os.readlink(base / "config/autorandr" / old)
module.save(base, key)
assert not (base / "config/autorandr" / old_target).exists()
assert module.profile(base, key) == old
world.fail_save = True
try:
    module.save(base, key)
    raise AssertionError("failed save accepted")
except RuntimeError:
    pass
world.fail_save = False
assert module.profile(base, key) == old
with module.locked(base, "edit"):
    try:
        with module.locked(base, "edit"):
            raise AssertionError("concurrent editor admitted")
    except module.Busy:
        pass
alias = base / "config/autorandr" / ("saved-" + "bad")
alias.symlink_to("../../outside")
try:
    module.profile(base, "bad")
    raise AssertionError("escaping profile admitted")
except RuntimeError:
    pass
alias.unlink()
unsafe = work / "unsafe"
unsafe.mkdir(mode=0o755)
try:
    module.private(unsafe)
    raise AssertionError("public directory admitted")
except RuntimeError:
    pass

# Actual independent watchdog processes with synthetic CLI and files.
original_choose = module.choose
for choice, kept in ((True, True), (False, False), (None, False)):
    world.current.write_text(one)
    module.choose = lambda *args, selected=choice, **kwargs: selected
    assert module.transaction(base, module.state(), lambda: world.command(["xrandr", "--test"]), True) == kept
    assert world.current.read_text() == (verbose([screen(x=100)]) if kept else one)
    assert not list(base.glob("rollback-*"))
world.current.write_text(one)
world.fail_apply = True
try:
    module.transaction(base, module.state(), lambda: world.command(["xrandr", "--test"]), True)
    raise AssertionError("apply failure accepted")
except RuntimeError:
    pass
assert world.current.read_text() == one
world.fail_apply = False
# Failure to start an independent watchdog prevents application altogether.
original_setsid = module.os.setsid
module.os.setsid = lambda: (_ for _ in ()).throw(OSError("synthetic watchdog startup failure"))
try:
    module.transaction(base, module.state(), lambda: world.command(["xrandr", "--test"]), True)
    raise AssertionError("unguarded application admitted")
except RuntimeError as error:
    assert "watchdog no está listo" in str(error)
finally:
    module.os.setsid = original_setsid
assert world.current.read_text() == one and not list(base.glob("rollback-*"))

# Known profiles are loaded without asking for confirmation.
module.choose = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected confirmation"))
assert module.transaction(base, module.state(), lambda: module.autorandr(base, "--load", old, "--force"), False)

# Timeout and parent EOF use the same real pipe protocol as a crash/termination.
for messages in (b"A", b""):
    backup = Path(module.tempfile.mkdtemp(dir=base, prefix="rollback-"))
    module.autorandr(backup, "--save", "rollback")
    read, write = os.pipe()
    if messages:
        os.write(write, messages)
    os.close(write)
    world.current.write_text(verbose([screen(x=100)]))
    assert module.guard(read, backup, key, 0.01, 0.01) == 1
    assert world.current.read_text() == one
    assert not backup.exists()

# Physical disconnect/reconnect never restores an old topology; rescue a dark one.
backup = Path(module.tempfile.mkdtemp(dir=base, prefix="rollback-"))
module.autorandr(backup, "--save", "rollback")
world.current.write_text(verbose([screen(enabled=False), screen("HDMI-1", enabled=False)]))
changed_key = module.identity(module.state())
read, write = os.pipe()
os.close(write)
assert module.guard(read, backup, key, 0.01, 0.01) == 1
assert module.identity(module.state()) == changed_key
assert any(value["enabled"] for value in module.state().values())
world.current.write_text(one)

# A failed atomic publication cannot damage the last confirmed profile.
original_replace = module.os.replace
previous = os.readlink(base / "config/autorandr" / old)
module.os.replace = lambda *args: (_ for _ in ()).throw(OSError("synthetic rename failure"))
try:
    module.save(base, key)
    raise AssertionError("failed publication accepted")
except OSError:
    pass
finally:
    module.os.replace = original_replace
assert os.readlink(base / "config/autorandr" / old) == previous
assert len(list((base / "config/autorandr").glob("version-*"))) == 1

# Disconnected but still configured CRTCs are cleared before autorandr snapshots.
world.current.write_text(one.replace("HDMI-9 disconnected", "HDMI-9 disconnected 1920x1080+0+0"))
assert module.identity(module.settle()) == key
assert "'HDMI-9', '--off'" in world.events.read_text()
world.current.write_text(one)

# Menu plumbing: arbitrary typed text never becomes an action/command.
class Menu:
    returncode = None
    terminated = False

    def __init__(self, argv, **kwargs):
        assert argv[0] == "dmenu" and "-c" in argv and argv[-2:] == ["-m", "2"]

    def communicate(self, data=None, timeout=None):
        self.returncode = 0
        return "not a listed choice\n", ""

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 1

    def kill(self):
        self.returncode = 1


original_popen = module.subprocess.Popen
module.subprocess.Popen = Menu
module.choose = original_choose
assert module.choose([("safe", "value")], "test", key, "2") is None
try:
    module.choose([("safe", "value")], "test", "different", "2")
    raise AssertionError("topology change ignored")
except module.TopologyChanged:
    pass
assert module.choose([("safe", "value")], "test", key, "2", timeout=0) is None
module.subprocess.Popen = original_popen

# Script the real editor: cancel is inert; apply+confirm saves automatically.
world.events.write_text("")
module.choose = lambda *args, **kwargs: None
module.configure(base, module.state())
assert "--save" not in world.events.read_text() and "--dryrun" not in world.events.read_text()
choices = iter(["apply", True])
module.choose = lambda *args, **kwargs: next(choices)
module.configure(base, module.state())
assert "--dryrun" in world.events.read_text() and "--save" in world.events.read_text()
assert module.profile(base, key) == old
world.fail_save = True
choices = iter(["apply", True, None, None])
module.choose = lambda *args, **kwargs: next(choices)
module.configure(base, module.state())
assert world.current.read_text() == verbose([screen(x=100)])
assert module.profile(base, key) == old
world.fail_save = False
world.current.write_text(one)

# Every editor control works on the draft only, using exact menu values.
def answers(values):
    choices = iter(values)

    def answer(options, *args, **kwargs):
        value = next(choices)
        assert value is None or value in [item[1] for item in options]
        return value

    return answer


edited = module.parse(two)
for name, choices in (
        ("HDMI-1", ["toggle"]), ("HDMI-1", ["toggle"]),
        ("HDMI-1", ["mode", "Cinema-wide"]), ("HDMI-1", ["rate", "50.00"]),
        ("HDMI-1", ["rotation", "left"]), ("HDMI-1", ["primary"]),
        ("HDMI-1", ["position", "DP-1", "below", 2])):
    module.choose = answers(choices)
    module.edit_output(edited, name, key, "2")
result = module.layout(edited)
assert result["HDMI-1"]["rotation"] == "left" and result["HDMI-1"]["primary"]
assert result["HDMI-1"]["relative"] == ("DP-1", "below", 2)
module.choose = answers(["position", "DP-1", "same"])
module.edit_output(edited, "HDMI-1", key, "2")
assert module.layout(edited)["HDMI-1"]["mode"] == "1920x1080"
module.choose = answers(["mode"])
try:
    module.edit_output(edited, "HDMI-1", key, "2")
    raise AssertionError("clone resolution silently changed")
except RuntimeError:
    pass
module.choose = answers(["position", None])
previous = copy.deepcopy(edited)
module.edit_output(edited, "HDMI-1", key, "2")
assert edited == previous

# Watcher debounce, no geometry loop, unknown cancel once, known reconnect.
class Done(Exception):
    pass


initial_configure, initial_transaction, initial_sleep = module.configure, module.transaction, module.time.sleep
actions = []
module.configure = lambda base, current, monitor=None: actions.append(("new", module.identity(current)))
module.transaction = lambda base, current, apply, confirm, monitor=None: actions.append(("known", module.identity(current)))
sequence = iter([one, verbose([screen(x=500)]), two, two, two, one, one])
world.current.write_text(one)


def tick(seconds):
    assert seconds == 2
    try:
        world.current.write_text(next(sequence))
    except StopIteration:
        raise Done


module.time.sleep = tick
try:
    module.watch(base)
except Done:
    pass
assert actions == [("known", key), ("new", module.identity(module.parse(two))), ("known", key)]
module.configure, module.transaction, module.time.sleep = initial_configure, initial_transaction, initial_sleep
module.choose, module.command = original_choose, original_command
print("PASS: display parsing/layouts, private atomic profiles, locks, editor, watchdog rollback and hotplug (no X)")
