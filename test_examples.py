"""
End-to-end tests: run each example .dnl file through the CLI and check
stdout / exit code. This exercises the full lexer -> parser -> type
checker -> interpreter pipeline exactly as a user would run it.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DANILIUM = ROOT / "danilium.py"
EXAMPLES = ROOT / "examples"


def run(path):
    return subprocess.run(
        [sys.executable, str(DANILIUM), str(path)],
        capture_output=True,
        text=True,
    )


def test_hello_world():
    result = run(EXAMPLES / "hello_world.dnl")
    assert result.returncode == 0
    assert result.stdout == "Hello, World!\n"


def test_hello_with_variable():
    result = run(EXAMPLES / "hello.dnl")
    assert result.returncode == 0
    assert result.stdout == "Hello, Danilium\n"


def test_conditions():
    result = run(EXAMPLES / "conditions.dnl")
    assert result.returncode == 0
    assert result.stdout == "Adult\nHot\n"


def test_loop():
    result = run(EXAMPLES / "loop.dnl")
    assert result.returncode == 0
    assert result.stdout == "0\n1\n2\n3\n4\ndone\n"


def test_functions():
    result = run(EXAMPLES / "functions.dnl")
    assert result.returncode == 0
    assert result.stdout == "25\n50\n"


def test_block_scoping_error():
    """A variable introduced inside `if` must not be visible after `end`."""
    result = run(EXAMPLES / "scoping.dnl")
    assert result.returncode == 1
    assert "Undefined variable 'y'" in result.stdout


def test_fixed_type_error():
    """Reassigning a variable with a different type is a type error."""
    result = run(EXAMPLES / "type_error.dnl")
    assert result.returncode == 1
    assert "Type mismatch at line 1" in result.stdout
