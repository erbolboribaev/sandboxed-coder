"""Command-line entry point: solve one problem and print the result.

Usage:
    python -m src.cli --problem problems/two_sum.json
"""
import argparse
import json
import time
import uuid

from dotenv import load_dotenv

from src.agent import solve

load_dotenv()  # reads .env into os.environ, so GROQ_API_KEY no longer
                # needs a manual `export` in every new terminal session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", required=True,
                         help="Path to a JSON file with 'problem' and 'test_code' keys")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-cost", type=float, default=0.50)
    args = parser.parse_args()

    spec = json.loads(open(args.problem).read())
    run_id = f"{spec.get('name', 'run')}_{uuid.uuid4().hex[:8]}"

    print(f"Solving: {spec.get('name', args.problem)}")
    start = time.time()
    result = solve(spec["problem"], spec["test_code"], run_id,
                    max_steps=args.max_steps, max_cost_usd=args.max_cost)
    elapsed = time.time() - start

    status = "SOLVED" if result.solved else "FAILED"
    print(f"\n{status} in {result.steps} step(s), ${result.total_cost_usd:.4f}, {elapsed:.1f}s")
    print(f"Stop reason: {result.stop_reason}")
    if result.final_code:
        print(f"\nFinal code:\n{result.final_code}")


if __name__ == "__main__":
    main()
