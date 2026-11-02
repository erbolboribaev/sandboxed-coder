"""Executes untrusted, LLM-generated code inside an isolated Docker
container: no network access, capped memory/CPU, and a hard wall-clock
timeout. This -- not the static safety check -- is what actually makes it
safe to run code we didn't write and don't fully trust.
"""
import tempfile
from dataclasses import dataclass
from pathlib import Path

import docker
import docker.errors
import requests.exceptions

IMAGE = "python:3.12-slim"
TIMEOUT_SECONDS = 5
MEMORY_LIMIT = "128m"
CPU_FRACTION = 0.5


@dataclass
class RunResult:
    passed: bool
    stdout: str
    stderr: str
    timed_out: bool


def run(code: str, test_code: str) -> RunResult:
    """code: the candidate solution. test_code: assertions to run against
    it. Both are concatenated into one script; success is "exits 0 and
    prints the sentinel", not just "exit 0", so a script that silently
    does nothing doesn't look like a pass.

    If Docker itself is unavailable (daemon not running, a transient
    named-pipe/socket hiccup), this is reported as a normal failed
    RunResult rather than raised -- from the agent's perspective, "the
    sandbox couldn't confirm this code works" is the same kind of failure
    whether the code was wrong or the infrastructure blipped, and callers
    (agent.solve(), scripts/run_benchmark.py) already know how to handle a
    failed run without crashing.
    """
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        return RunResult(passed=False, stdout="",
                          stderr=f"Docker unavailable: {e}", timed_out=False)

    script = f"{code}\n\n{test_code}\n\nprint('ALL_TESTS_PASSED')\n"
    container = None

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "run.py").write_text(script)

        try:
            container = client.containers.run(
                IMAGE,
                command=["python", "/sandbox/run.py"],
                volumes={tmp: {"bind": "/sandbox", "mode": "ro"}},
                working_dir="/sandbox",
                network_disabled=True,
                mem_limit=MEMORY_LIMIT,
                nano_cpus=int(CPU_FRACTION * 1e9),
                detach=True,
            )
            timed_out = False
            try:
                container.wait(timeout=TIMEOUT_SECONDS)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                # On Windows, Docker Desktop talks over a named pipe rather
                # than a normal TCP/unix socket; a client-side read timeout
                # there surfaces as ConnectionError (wrapping a
                # urllib3.ReadTimeoutError), not requests.ReadTimeout as it
                # does on Linux/Mac. Catch both, since which one you get is
                # a transport/OS detail, not something callers should have
                # to know. Either way, the container is still running in
                # the Docker engine and must be killed explicitly, or it
                # keeps burning CPU/memory.
                timed_out = True
                container.kill()

            stdout = container.logs(stdout=True, stderr=False).decode(errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode(errors="replace")
        except docker.errors.DockerException as e:
            # Docker was reachable a moment ago (from_env succeeded) but
            # failed mid-operation -- e.g. it was restarting. Same
            # treatment: a failed run, not a crash.
            return RunResult(passed=False, stdout="",
                              stderr=f"Docker error during run: {e}", timed_out=False)
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except docker.errors.DockerException:
                    pass  # best-effort cleanup; don't mask the real result over this

    passed = (not timed_out) and "ALL_TESTS_PASSED" in stdout
    return RunResult(passed=passed, stdout=stdout, stderr=stderr, timed_out=timed_out)
