"""Thin wrapper around the Groq API: sends a coding prompt, returns the
generated code plus token usage so the caller can track cost.

Pricing changes often -- verify current rates at https://console.groq.com/docs/models
before relying on the cost guardrail for real spending protection. The
defaults below are a best-effort snapshot (as of the project's creation)
and are safe to edit; keeping them in one dict means updating a price is a
one-line change, not a code change.
"""
import os
from dataclasses import dataclass

from groq import Groq

# USD per 1,000 tokens.
PRICING = {
    "openai/gpt-oss-20b": {"input": 0.000075, "output": 0.0003},
    "openai/gpt-oss-120b": {"input": 0.00015, "output": 0.0006},
}
DEFAULT_MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = (
    "You are a careful Python programmer. Given a problem statement, write "
    "a single Python function that solves it. Respond with ONLY a fenced "
    "python code block -- no explanation before or after. The function must "
    "be named exactly as specified in the problem. Do not import anything "
    "outside the Python standard library's math/collections/itertools/typing "
    "modules unless the problem explicitly requires it."
)


@dataclass
class Generation:
    code: str
    cost_usd: float
    input_tokens: int
    output_tokens: int


def extract_code(text: str) -> str:
    """Pull the content of the first ```python ... ``` (or bare ```) fenced
    block. Falls back to the raw text if the model didn't fence anything,
    since a stricter parser would just turn a formatting slip into a crash."""
    if "```" not in text:
        return text.strip()
    parts = text.split("```")
    for part in parts[1::2]:  # odd-indexed parts are inside fences
        body = part[6:].lstrip("\n") if part.startswith("python") else part
        if body.strip():
            return body.strip()
    return text.strip()


def generate_code(problem: str, history: list[dict] | None = None,
                   model: str = DEFAULT_MODEL) -> Generation:
    """history: prior [{"role": ..., "content": ...}] turns (e.g. a failed
    attempt plus the error it produced), appended after the problem
    statement so the model can see what it already tried."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": problem}]
    if history:
        messages += history

    resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
    usage = resp.usage
    price = PRICING.get(model, {"input": 0.0, "output": 0.0})
    cost = ((usage.prompt_tokens / 1000) * price["input"]
            + (usage.completion_tokens / 1000) * price["output"])

    return Generation(
        code=extract_code(resp.choices[0].message.content),
        cost_usd=cost,
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
    )
