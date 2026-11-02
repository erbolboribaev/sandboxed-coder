"""Static safety check: rejects obviously dangerous code before it ever
reaches the sandbox. This is defense in depth, not the primary guard --
Docker's network/filesystem isolation (sandbox.py) is what actually makes
execution safe. This check exists to fail fast with a clear reason, rather
than relying solely on the sandbox boundary holding.
"""
import ast

BANNED_IMPORTS = {"os", "sys", "subprocess", "socket", "shutil", "ctypes",
                   "requests", "urllib", "http", "ftplib", "telnetlib", "pathlib"}
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "open"}


class UnsafeCodeError(Exception):
    pass


def check(code: str) -> None:
    """Raises UnsafeCodeError if the code imports or calls anything banned.
    A SyntaxError propagates uncaught -- the caller treats that as a failed
    attempt to fix, not a safety violation.
    """
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_IMPORTS:
                    raise UnsafeCodeError(f"banned import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in BANNED_IMPORTS:
                raise UnsafeCodeError(f"banned import: {node.module}")
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
            if name in BANNED_CALLS:
                raise UnsafeCodeError(f"banned call: {name}")
