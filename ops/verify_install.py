"""Clean, offline wheel install; fixtures are input files, not imported repo code."""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--allow-downloads", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="launchcase-wheel-") as temporary:
    folder = Path(temporary).resolve()
    requirements = folder / "requirements.txt"

    def run(*args, cwd=folder):
        subprocess.run(
            args,
            cwd=cwd,
            check=True,
            env={**os.environ, "PYTHONPATH": ""},
            stdout=subprocess.DEVNULL if args[:2] == ("uv", "export") else None,
        )

    run(
        "uv",
        "export",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--output-file",
        str(requirements),
        cwd=root,
    )
    run("uv", "venv", "--python", sys.executable, str(folder / "venv"))
    python = folder / "venv/bin/python"
    run(
        "uv",
        "pip",
        "install",
        *([] if args.allow_downloads else ["--offline"]),
        "--python",
        str(python),
        "-r",
        str(requirements),
        str(root / "dist/launchcase-0.1.0-py3-none-any.whl"),
    )
    cli = str(folder / "venv/bin/launchcase")
    run(cli, "doctor")
    run(
        cli,
        "demo",
        "--fixture",
        str(root / "fixtures/scenarios/pet-furniture-us"),
        "--out",
        str(folder / "demo"),
    )
    run(cli, "validate", "--case", str(folder / "demo"), "--strict")
    print(
        "Clean wheel resources/migrations/Skills/Mock raster and no-paid-services journey verified outside repo."
    )
