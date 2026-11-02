"""Runs the agent over every problem in problems/*.json and prints a
summary: success rate, average steps/cost for solved problems, and which
problems failed and why.

    python scripts/run_benchmark.py

Results are saved incrementally to logs/benchmark_results.json after each
problem (not just at the end) -- a crash or interruption partway through
still leaves everything completed so far on disk.
"""
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import docker
import docker.errors
from dotenv import load_dotenv

from src.agent import solve

load_dotenv()

PROBLEMS_DIR = Path("problems")
RESULTS_PATH = Path("logs/benchmark_results.json")


def check_docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except docker.errors.DockerException:
        return False


def main():
    problem_files = sorted(PROBLEMS_DIR.glob("*.json"))
    if not problem_files:
        print(f"No problems found in {PROBLEMS_DIR}/. Run "
              f"scripts/generate_problems.py first.")
        return

    if not check_docker_available():
        print("Docker is not reachable right now (daemon not running, or "
              "still starting up). Start/restart Docker Desktop, confirm "
              "`docker ps` works, then rerun this script.")
        return

    results = []
    print(f"Running benchmark over {len(problem_files)} problems...\n")

    for path in problem_files:
        spec = json.loads(path.read_text())
        run_id = f"bench_{spec['name']}_{uuid.uuid4().hex[:8]}"

        start = time.time()
        try:
            result = solve(spec["problem"], spec["test_code"], run_id)
            entry = {
                "name": spec["name"],
                "solved": result.solved,
                "steps": result.steps,
                "cost_usd": result.total_cost_usd,
                "elapsed_s": round(time.time() - start, 2),
                "stop_reason": result.stop_reason,
            }
        except Exception as e:
            # An unexpected error on one problem (e.g. Docker dying mid-run)
            # must not take the rest of the benchmark down with it -- record
            # it as a failure and keep going.
            entry = {
                "name": spec["name"],
                "solved": False,
                "steps": 0,
                "cost_usd": 0.0,
                "elapsed_s": round(time.time() - start, 2),
                "stop_reason": f"crashed: {type(e).__name__}: {e}",
            }

        status = "SOLVED" if entry["solved"] else "FAILED"
        print(f"[{status:>6}] {spec['name']:<28} "
              f"steps={entry['steps']} cost=${entry['cost_usd']:.4f} "
              f"{entry['elapsed_s']:.1f}s  ({entry['stop_reason']})")

        results.append(entry)
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULTS_PATH.write_text(json.dumps(results, indent=2))  # saved after every problem

    print_summary(results)
    print(f"\nFull results saved to {RESULTS_PATH}")


def print_summary(results: list[dict]) -> None:
    total = len(results)
    solved = [r for r in results if r["solved"]]
    failed = [r for r in results if not r["solved"]]

    print(f"\n{'=' * 50}")
    print(f"Success rate: {len(solved)}/{total} ({len(solved) / total:.0%})")

    if solved:
        avg_steps = sum(r["steps"] for r in solved) / len(solved)
        first_try = sum(1 for r in solved if r["steps"] == 1)
        print(f"Avg steps to solve: {avg_steps:.1f}  "
              f"(solved on first try: {first_try}/{len(solved)})")

    total_cost = sum(r["cost_usd"] for r in results)
    print(f"Total cost: ${total_cost:.4f}")

    if failed:
        print("\nFailed:")
        for r in failed:
            print(f"  - {r['name']}: {r['stop_reason']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
