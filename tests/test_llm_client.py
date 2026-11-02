from src.llm_client import extract_code


def test_extracts_python_fenced_block():
    text = "Here is the code:\n```python\ndef f():\n    return 1\n```\nDone."
    assert extract_code(text) == "def f():\n    return 1"


def test_extracts_bare_fenced_block():
    text = "```\ndef f():\n    return 1\n```"
    assert extract_code(text) == "def f():\n    return 1"


def test_falls_back_to_raw_text_when_no_fence():
    text = "def f():\n    return 1"
    assert extract_code(text) == text
