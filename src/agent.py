"""The agent loop: generate code, run it in the sandbox, and on failure feed
the error back to the model for another attempt -- bounded by hard limits
(max steps, max cost) so a stuck agent can't loop forever or spend without
bound. Every step is logged as one JSON line for later analysis.
"""
import json
from dataclasses import dataclass
from pathlib import Path

from src import llm_client, sandbox
from src.safety_check import UnsafeCodeError, check as safety_check

MAX_STEPS = 5
MAX_COST_USD = 0.50
LOG_PATH = Path("logs/runs.jsonl")


@dataclass
class AgentResult:
    solved: bool
    steps: int
    total_cost_usd: float
    final_code: str | None
    stop_reason: str


def solve(problem: str, test_code: str, run_id: str,
          max_steps: int = MAX_STEPS, max_cost_usd: float = MAX_COST_USD,
          generate_fn=llm_client.generate_code, run_fn=sandbox.run,
          log_path: Path = LOG_PATH) -> AgentResult:
    """generate_fn/run_fn are injectable so the control-flow logic (step
    limit, cost limit, retry-on-failure) can be unit-tested without a real
    LLM call or a real Docker container.
    """
    history: list[dict] = []
    total_cost = 0.0
    last_code = None

    for step in range(1, max_steps + 1):
        gen = generate_fn(problem, history=history or None)
        total_cost += gen.cost_usd
        last_code = gen.code
        event = {"run_id": run_id, "step": step, "cost_usd": gen.cost_usd,
                  "total_cost_usd": total_cost, "code": gen.code}

        if total_cost > max_cost_usd:
            event["stop_reason"] = "cost_budget_exceeded"
            _log(event, log_path)
            return AgentResult(False, step, total_cost, gen.code, "cost_budget_exceeded")

        try:
            safety_check(gen.code)
        except UnsafeCodeError as e:
            # Don't retry on unsafe code: feeding it back and hoping for a
            # safer rewrite is a weaker guarantee than simply stopping.
            event["stop_reason"] = f"unsafe_code: {e}"
            _log(event, log_path)
            return AgentResult(False, step, total_cost, gen.code, f"unsafe_code: {e}")
        except SyntaxError as e:
            event["result"] = f"SyntaxError: {e}"
            _log(event, log_path)
            history += [
                {"role": "assistant", "content": f"```python\n{gen.code}\n```"},
                {"role": "user", "content": f"That code had a syntax error: {e}. Please fix it."},
            ]
            continue

        run_result = run_fn(gen.code, test_code)
        event.update(passed=run_result.passed, stdout=run_result.stdout,
                      stderr=run_result.stderr, timed_out=run_result.timed_out)
        _log(event, log_path)

        if run_result.passed:
            return AgentResult(True, step, total_cost, gen.code, "solved")

        feedback = ("Execution timed out -- it likely has an infinite loop."
                    if run_result.timed_out
                    else f"Tests failed. Output:\n{run_result.stdout}\n{run_result.stderr}")
        history += [
            {"role": "assistant", "content": f"```python\n{gen.code}\n```"},
            {"role": "user", "content": f"{feedback}\nPlease fix the code."},
        ]

    return AgentResult(False, max_steps, total_cost, last_code, "max_steps_exceeded")


def _log(event: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(event, default=str) + "\n")
