"""Reproducible Windows packaging without unrelated DLLs inherited from PATH."""

from pathlib import Path
import os, subprocess, sys
import PySide6, shiboken6

ROOT = Path(__file__).resolve().parent
windows = Path(os.environ.get("SystemRoot", "C:/Windows"))
env = os.environ.copy()
env["PATH"] = os.pathsep.join(
    map(
        str,
        [
            Path(sys.executable).parent,
            Path(sys.base_prefix),
            Path(PySide6.__file__).parent,
            Path(shiboken6.__file__).parent,
            windows / "System32",
            windows,
        ],
    )
)
mode = "--console" if "--diagnostic" in sys.argv else "--windowed"
command = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--onefile",
    mode,
    "--name",
    "Sanad",
    "--icon",
    str(ROOT / "assets/icon.ico"),
    "--add-data",
    str(ROOT / "assets") + ":assets",
    "--distpath",
    str(ROOT / "release"),
    "--workpath",
    str(ROOT / "build/work"),
    "--specpath",
    str(ROOT / "build"),
    str(ROOT / "main.py"),
]
subprocess.run(command, cwd=ROOT, env=env, check=True)
