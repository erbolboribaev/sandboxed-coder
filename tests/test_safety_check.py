import pytest

from src.safety_check import check, UnsafeCodeError


def test_safe_code_passes():
    check("def add(a, b):\n    return a + b")


def test_banned_import_rejected():
    with pytest.raises(UnsafeCodeError):
        check("import os\ndef f():\n    os.system('rm -rf /')")


def test_banned_import_from_rejected():
    with pytest.raises(UnsafeCodeError):
        check("from subprocess import run\ndef f():\n    run(['ls'])")


def test_banned_call_eval_rejected():
    with pytest.raises(UnsafeCodeError):
        check("def f(x):\n    return eval(x)")


def test_banned_call_open_rejected():
    with pytest.raises(UnsafeCodeError):
        check("def f():\n    open('/etc/passwd').read()")


def test_allowed_stdlib_passes():
    check("import math\nimport collections\ndef f(x):\n    return math.sqrt(x)")


def test_syntax_error_propagates():
    with pytest.raises(SyntaxError):
        check("def f(:\n    pass")
