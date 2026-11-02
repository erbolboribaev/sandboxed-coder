with open("scripts/docker_smoke_test.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''    r4 = run("import socket\\nsocket.socket()", "")
    network_blocked = "Network is unreachable" in r4.stderr or not r4.passed
    print(f"[{'OK' if network_blocked else 'FAIL'}] network access is blocked inside the container")
    all_ok &= network_blocked'''

new = '''    # socket.socket() alone never touches the network -- it just
    # allocates a local object. The check needs an actual connect()
    # attempt, or it "passes" regardless of whether isolation works.
    r4 = run(
        "import socket\\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\\n"
        "s.settimeout(3)\\n"
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
    all_ok &= network_blocked'''

assert old in content, "pattern not found"
content = content.replace(old, new)
with open("scripts/docker_smoke_test.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed.")
