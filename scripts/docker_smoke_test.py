"""Run this FIRST, before anything else, to confirm Docker sandboxing
actually works on this machine: python scripts/docker_smoke_test.py

Does NOT call Groq or cost anything -- it only exercises src/sandbox.py
with hardcoded code, covering the pass, fail, and timeout cases.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sandbox import run


def check(label, result, expect_passed, expect_timed_out=False):
    ok = (result.passed == expect_passed) and (result.timed_out == expect_timed_out)
    print(f"[{'OK' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"       passed={result.passed} timed_out={result.timed_out}")
        print(f"       stdout={result.stdout!r}")
        print(f"       stderr={result.stderr!r}")
    return ok


def main():
    print("Testing Docker sandbox (this pulls python:3.12-slim on first run, "
          "which can take a minute)...\n")

    all_ok = True

    r1 = run("def add(a, b):\n    return a + b", "assert add(2, 3) == 5")
    all_ok &= check("passing code is reported as passed", r1, expect_passed=True)

    r2 = run("def add(a, b):\n    return a - b", "assert add(2, 3) == 5")
    all_ok &= check("failing assertion is reported as failed", r2, expect_passed=False)

    r3 = run("while True:\n    pass", "")
    all_ok &= check("infinite loop is caught by the timeout",
                     r3, expect_passed=False, expect_timed_out=True)

    # socket.socket() alone never touches the network -- it just
    # allocates a local object. The check needs an actual connect()
    # attempt, or it "passes" regardless of whether isolation works.
    r4 = run(
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.settimeout(3)\n"
        "s.connect(('8.8.8.8', 53))",
        "",
    )
    network_blocked = not r4.passed and (
        "Network is unreachable" in r4.stderr or "unreachable" in r4.stderr.lower()
        or r4.timed_out
    )
    print(f"[{'OK' if network_blocked else 'FAIL'}] network access is blocked inside the container")
    if not network_blocked:
        print(f"       passed={r4.passed} timed_out={r4.timed_out}")
        print(f"       stderr={r4.stderr!r}")
    all_ok &= network_blocked

    print(f"\n{'All checks passed.' if all_ok else 'SOME CHECKS FAILED -- see above.'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
