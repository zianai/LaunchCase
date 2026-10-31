"""Cross-repository test adapter uses process/HTTP boundaries only, never imports CE."""

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ui", action="store_true")
    parser.add_argument("--suite", choices=["sku", "handoff", "regression"], default="sku")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    engine = args.engine_repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    data = root / ".launchcase" / ("engine-test-" + str(time.time_ns()))
    data.mkdir(parents=True, mode=0o700)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "PLAYWRIGHT_BROWSERS_PATH")
        if key in os.environ
    }
    env.update(
        {
            "CREATIVE_DATA_DIR": str(data),
            "CREATIVE_API_TOKEN": "launchcase-isolated-test-token",
            "PORT": str(port),
            "ALLOW_TEST_LIVE": "off",
            "OPENAI_AGENTS_DISABLE_TRACING": "1",
        }
    )
    url = f"http://127.0.0.1:{port}"
    with (out / "engine.log").open("w") as log:
        process = subprocess.Popen(
            ["node", "node_modules/tsx/dist/cli.mjs", "scripts/p10-local.ts"],
            cwd=engine,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            for _ in range(150):
                if process.poll() is not None:
                    raise RuntimeError("Isolated CE exited; inspect engine.log")
                try:
                    request = Request(
                        url + "/v1/health", headers={"Authorization": "Bearer launchcase-isolated-test-token"}
                    )
                    with build_opener(ProxyHandler({})).open(request, timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("Isolated CE readiness timeout")
            env.update(
                {
                    "LAUNCHCASE_TEST_ENGINE_HTTP": "1",
                    "LAUNCHCASE_TEST_ENGINE_URL": url,
                    "LAUNCHCASE_TEST_ENGINE_TOKEN": "launchcase-isolated-test-token",
                }
            )
            if args.ui:
                command = [
                    sys.executable,
                    "ops/verify_p8_p10_ui.py",
                    "--engine-url",
                    url,
                    "--out",
                    str(out / "browser"),
                    "--suite",
                    args.suite,
                ]
            else:
                command = [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_p7_sku.py",
                    "tests/test_visuals.py",
                    "-q",
                ]
            return subprocess.run(command, cwd=root, env=env).returncode
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
