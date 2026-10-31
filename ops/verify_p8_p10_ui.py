"""Disposable API+browser drill. Caller supplies an isolated loopback CE Mock URL.

No credentials are inherited, no genuine business data is loaded, and no service
is exposed outside loopback. The fixture exercises real-mode *contracts* only.
"""

import argparse
import base64
import io
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from conftest import brief, setup  # noqa: E402
from PIL import Image  # noqa: E402
from test_handoff import real_mode  # noqa: E402
from test_p7_sku import sku  # noqa: E402


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait(url, process):
    for _ in range(180):
        if process.poll() is not None:
            raise RuntimeError("Local service exited; inspect isolated service log")
        try:
            with build_opener(ProxyHandler({})).open(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.2)
    raise RuntimeError("Local service readiness timeout")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-url", required=True)
    parser.add_argument("--suite", choices=["sku", "handoff", "regression"], default="sku")
    parser.add_argument("--engine-token", default="launchcase-isolated-test-token")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    parsed = urlsplit(args.engine_url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise ValueError("An isolated numeric loopback Engine is required")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    data = ROOT / ".launchcase" / ("p8-p10-" + str(time.time_ns()))
    data.mkdir(parents=True, mode=0o700)
    base = real_mode.__wrapped__(setup.__wrapped__(data), brief.__wrapped__())
    svc, actor, case, sample_request, _ = base
    token, _ = svc.provision(actor.tenant_id, "TEST ONLY browser operator", "owner", False)
    (data / "token").write_text(token)
    (data / "token").chmod(0o600)
    manifest = {
        "case_id": case["id"],
        "database": str(data / "test.db"),
        "data_dir": str(data),
        "sample": sample_request.model_dump(),
        "scope": "TEST ONLY fictional contract fixture; not E3",
    }
    if args.suite == "sku":
        fixture = sku.__wrapped__(base)
        _, _, _, _, upload, sample, rule, concept = fixture
        cutout = base64.b64decode(upload.data_base64)
        (data / "TEST-ONLY-cutout.png").write_bytes(cutout)
        with Image.open(io.BytesIO(cutout)) as image:
            photo = Image.new("RGB", image.size, "white")
            photo.paste(image, mask=image.getchannel("A"))
            photo.save(data / "TEST-ONLY-original.png")
        manifest.update(
            {"upload": upload.model_dump(), "sample": sample, "rule": rule, "concept_id": concept}
        )
    (data / "manifest.json").write_text(json.dumps(manifest, indent=2))
    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "PLAYWRIGHT_BROWSERS_PATH")
        if key in os.environ
    }
    api_port, web_port = port(), port()
    env.update(
        {
            "OPENAI_AGENTS_DISABLE_TRACING": "1",
            "NEXT_TELEMETRY_DISABLED": "1",
            "ALLOW_TEST_LIVE": "off",
            "LAUNCHCASE_DATA_DIR": str(data),
            "LAUNCHCASE_DATABASE_URL": f"sqlite:///{data}/test.db",
            "LAUNCHCASE_CREATIVE_ENGINE_MODE": "http",
            "LAUNCHCASE_CREATIVE_ENGINE_URL": args.engine_url,
            "LAUNCHCASE_CREATIVE_ENGINE_TOKEN": args.engine_token,
            "LAUNCHCASE_API_URL": f"http://127.0.0.1:{api_port}",
            "LAUNCHCASE_WEB_URL": f"http://127.0.0.1:{web_port}",
            "LAUNCHCASE_P8_SEED": str(data),
            "LAUNCHCASE_HANDOFF_DIR": str(data),
            "LAUNCHCASE_TOKEN_FILE": str(data / "token"),
            "LAUNCHCASE_SCREENSHOT_DIR": str(out),
        }
    )
    processes = []
    try:
        with (out / "api.log").open("w") as apilog, (out / "web.log").open("w") as weblog:
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "launchcase.api:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(api_port),
                        "--no-access-log",
                    ],
                    cwd=ROOT,
                    env=env,
                    stdout=apilog,
                    stderr=subprocess.STDOUT,
                )
            )
            wait(env["LAUNCHCASE_API_URL"] + "/health", processes[-1])
            processes.append(
                subprocess.Popen(
                    [
                        "node",
                        "node_modules/next/dist/bin/next",
                        "start",
                        "--hostname",
                        "127.0.0.1",
                        "--port",
                        str(web_port),
                    ],
                    cwd=ROOT / "frontend",
                    env=env,
                    stdout=weblog,
                    stderr=subprocess.STDOUT,
                )
            )
            wait(env["LAUNCHCASE_WEB_URL"], processes[-1])
            result = subprocess.run(
                [
                    "node",
                    "node_modules/@playwright/test/cli.js",
                    "test",
                    "-c",
                    {
                        "sku": "playwright.p8-p10.config.ts",
                        "handoff": "playwright.handoff.config.ts",
                        "regression": "playwright.config.ts",
                    }[args.suite],
                ],
                cwd=ROOT / "frontend",
                env=env,
            )
            return result.returncode
    finally:
        for p in reversed(processes):
            p.terminate()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        (data / "token").unlink(missing_ok=True)
        svc.engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
