"""Native Lua power storage on synthetic GIO files; no display or system/session bus."""
import json
import os
from pathlib import Path
import subprocess
import sys

root, temporary = map(Path, sys.argv[1:])
assert not any(os.environ.get(key) for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS"))
for case in ("missing", "valid", "invalid", "oversize", "symlink", "ancestor", "hardlink", "directory", "malformed"):
    base = temporary / ("native-power-" + case)
    base.mkdir(mode=0o700)
    config = base / "config"
    config.mkdir(mode=0o700)
    directory = config / "wm/awesome"
    path = directory / "power.json"
    sentinel = base / "sentinel"
    sentinel.write_text('{"aclid":"lock"}')
    sentinel.chmod(0o600)
    if case != "missing":
        directory.mkdir(parents=True, mode=0o700)
        if case == "symlink":
            path.symlink_to(sentinel)
        elif case == "ancestor":
            directory.rmdir()
            target = base / "target"
            target.mkdir(mode=0o700)
            directory.symlink_to(target, target_is_directory=True)
        elif case == "hardlink":
            os.link(sentinel, path)
        elif case == "directory":
            path.mkdir(mode=0o700)
        else:
            contents = {"valid": json.dumps({"aclid": "lock", "aclock": "900"}),
                        "invalid": '{"acsuspend":"777"}', "oversize": "x" * 8193,
                        "malformed": '{"aclid":'}[case]
            path.write_text(contents)
            path.chmod(0o600)
    environment = dict(os.environ, XDG_CONFIG_HOME=str(config))
    subprocess.run(["lua5.3", str(root / "awesome/tests/power-storage.lua"), str(root), case],
                   env=environment, check=True, timeout=15)
    assert sentinel.read_text() == '{"aclid":"lock"}'
    if case in ("missing", "valid"):
        assert path.stat().st_mode & 0o777 == 0o600
        assert json.loads(path.read_text())["batterylid"] == "suspend"
        assert directory.stat().st_mode & 0o077 == 0
    elif case in ("invalid", "oversize", "malformed"):
        assert path.read_text() == contents
print("PASS: native power persistence, async GIO, schema, private atomic saves, cancellation and hostile paths (synthetic files only)")
