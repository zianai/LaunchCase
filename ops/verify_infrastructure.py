"""Isolated disposable PostgreSQL/Redis smoke; never touches existing containers."""

import json
import os
import subprocess
import sys
import time
from uuid import uuid4

import psycopg

suffix = uuid4().hex[:8]
names = []
pull_policy = ["--pull=never"] if os.environ.get("P7_OFFLINE_DOCKER") == "1" else []
try:
    ports = {}
    for kind, image, inside in [
        ("pg", "postgres:17.6-bookworm", 5432),
        ("redis", "redis:7.4.6-alpine", 6379),
    ]:
        name = f"launchcase-p6-{kind}-{suffix}"
        cmd = ["docker", "run", *pull_policy, "--rm", "-d", "--name", name, "-p", f"127.0.0.1::{inside}"]
        if kind == "pg":
            cmd += ["-e", "POSTGRES_PASSWORD=launchcase-test-only", "-e", "POSTGRES_DB=launchcase"]
        cmd += [image]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        names.append(name)
        info = json.loads(subprocess.check_output(["docker", "inspect", name]))[0]
        ports[kind] = info["NetworkSettings"]["Ports"][f"{inside}/tcp"][0]["HostPort"]
    ready = False
    for _ in range(50):
        try:
            # The image's bootstrap Unix socket can be ready before its final TCP server.
            # Probe the exact mapped endpoint used by the application, not that temporary socket.
            with psycopg.connect(
                host="127.0.0.1",
                port=int(ports["pg"]),
                dbname="launchcase",
                user="postgres",
                password="launchcase-test-only",
                connect_timeout=1,
            ) as connection:
                connection.execute("SELECT 1")
                ready = True
                break
        except psycopg.Error:
            pass
        time.sleep(0.2)
    if not ready:
        raise RuntimeError("Isolated PostgreSQL did not start")
    env = dict(
        os.environ,
        LAUNCHCASE_TEST_POSTGRES=f"postgresql+psycopg://postgres:launchcase-test-only@127.0.0.1:{ports['pg']}/launchcase",
        LAUNCHCASE_TEST_REDIS_PORT=ports["redis"],
    )
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_infrastructure.py"], env=env)
    print(
        json.dumps(
            {"scope": "isolated PostgreSQL/Redis/ARQ", "exit_code": result.returncode, "containers": names}
        )
    )
    sys.exit(result.returncode)
finally:
    for name in names:
        subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
