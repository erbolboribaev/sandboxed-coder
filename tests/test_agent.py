"""Tests the agent loop's control flow (step limit, cost limit, retry,
unsafe-code short-circuit) using fake generate_fn/run_fn -- no real LLM
call or Docker container involved, so this suite runs in CI without a
GROQ_API_KEY or a Docker daemon.
"""
import json

import pytest

from src.agent import solve
from src.llm_client import Generation
from src.sandbox import RunResult


def gen(code, cost=0.01):
    return Generation(code=code, cost_usd=cost, input_tokens=10, output_tokens=10)


def test_solves_on_first_try(tmp_path):
    def fake_generate(problem, history=None):
        return gen("def add(a, b):\n    return a + b")

    def fake_run(code, test_code):
        return RunResult(passed=True, stdout="ALL_TESTS_PASSED", stderr="", timed_out=False)

    result = solve("add two numbers", "assert add(1, 2) == 3", run_id="t1",
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert result.solved
    assert result.steps == 1
    assert result.stop_reason == "solved"


def test_retries_then_solves(tmp_path):
    attempts = {"n": 0}

    def fake_generate(problem, history=None):
        attempts["n"] += 1
        return gen(f"def add(a, b):\n    return a + b  # attempt {attempts['n']}")

    def fake_run(code, test_code):
        if attempts["n"] < 3:
            return RunResult(passed=False, stdout="", stderr="AssertionError", timed_out=False)
        return RunResult(passed=True, stdout="ALL_TESTS_PASSED", stderr="", timed_out=False)

    result = solve("add", "assert True", run_id="t2",
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert result.solved
    assert result.steps == 3
    assert attempts["n"] == 3


def test_stops_at_max_steps(tmp_path):
    def fake_generate(problem, history=None):
        return gen("def add(a, b):\n    return a - b  # always wrong")

    def fake_run(code, test_code):
        return RunResult(passed=False, stdout="fail", stderr="", timed_out=False)

    result = solve("add", "assert True", run_id="t3", max_steps=3,
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert not result.solved
    assert result.steps == 3
    assert result.stop_reason == "max_steps_exceeded"


def test_stops_at_cost_budget(tmp_path):
    def fake_generate(problem, history=None):
        return gen("def f(): pass", cost=0.30)

    def fake_run(code, test_code):
        return RunResult(passed=False, stdout="fail", stderr="", timed_out=False)

    result = solve("f", "assert True", run_id="t4", max_cost_usd=0.50,
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert not result.solved
    assert result.stop_reason == "cost_budget_exceeded"
    assert result.steps == 2


def test_unsafe_code_stops_immediately_no_retry(tmp_path):
    calls = {"n": 0}

    def fake_generate(problem, history=None):
        calls["n"] += 1
        return gen("import os\nos.system('echo hi')")

    def fake_run(code, test_code):
        raise AssertionError("run_fn should never be called for unsafe code")

    result = solve("f", "assert True", run_id="t5",
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert not result.solved
    assert "unsafe_code" in result.stop_reason
    assert calls["n"] == 1


def test_timeout_is_treated_as_failure_and_retried(tmp_path):
    attempts = {"n": 0}

    def fake_generate(problem, history=None):
        attempts["n"] += 1
        return gen("while True: pass")

    def fake_run(code, test_code):
        if attempts["n"] == 1:
            return RunResult(passed=False, stdout="", stderr="", timed_out=True)
        return RunResult(passed=True, stdout="ALL_TESTS_PASSED", stderr="", timed_out=False)

    result = solve("f", "assert True", run_id="t6",
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert result.solved
    assert result.steps == 2


def test_log_file_records_every_step(tmp_path):
    log_path = tmp_path / "runs.jsonl"

    def fake_generate(problem, history=None):
        return gen("def f(): return 1")

    def fake_run(code, test_code):
        return RunResult(passed=True, stdout="ALL_TESTS_PASSED", stderr="", timed_out=False)

    solve("f", "assert True", run_id="t7",
          generate_fn=fake_generate, run_fn=fake_run, log_path=log_path)

    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["run_id"] == "t7"
    assert entry["passed"] is True


def test_docker_unavailable_is_treated_as_a_failed_run_not_a_crash(tmp_path):
    """Regression test for the Docker-hiccup bug found during the real
    benchmark run: sandbox.run() returning a failed RunResult (because
    Docker was unreachable) must flow through the normal retry/failure
    path, not raise and crash the caller."""
    def fake_generate(problem, history=None):
        return gen("def f(): return 1")

    def fake_run(code, test_code):
        return RunResult(passed=False, stdout="", stderr="Docker unavailable: ...", timed_out=False)

    result = solve("f", "assert True", run_id="t8", max_steps=2,
                    generate_fn=fake_generate, run_fn=fake_run,
                    log_path=tmp_path / "runs.jsonl")
    assert not result.solved
    assert result.stop_reason == "max_steps_exceeded"
