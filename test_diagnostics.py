"""CLI tests for the shared diagnostic format and output streams."""

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLI = ROOT / "danilium.py"


def run_source(source):
    with tempfile.TemporaryDirectory(prefix=".diag-test-", dir=ROOT) as temp_dir:
        path = Path(temp_dir) / "example.dnl"
        path.write_text(source, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(CLI), str(path)],
            capture_output=True,
            text=True,
        )
        return result, str(path)


def test_runtime_diagnostic_uses_shared_format_and_stderr():
    result, path = run_source("numbers = [10]\nrun(numbers[1])\n")
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "error: List index out of bounds\n"
        f"  --> {path}:2:12\n"
    )


def test_type_diagnostic_uses_shared_format_and_stderr():
    result, path = run_source('x = 1\nx = "hello"\n')
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "error: x is int, but you assigned a string.\n"
        f"  --> {path}:2:1\n"
    )


def test_lexer_diagnostic_includes_source_location():
    result, path = run_source("run(@)\n")
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "error: Unexpected character '@'\n"
        f"  --> {path}:1:5\n"
    )


def test_parser_diagnostic_includes_source_location():
    result, path = run_source("run(1\n")
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("error: Expected RPAREN")
    assert result.stderr.endswith(f"  --> {path}:1:6\n")


def test_successful_run_output_stays_on_stdout():
    result, _ = run_source('run("hello")\n')
    assert result.returncode == 0
    assert result.stdout == "hello\n"
    assert result.stderr == ""


def test_return_outside_function_is_rejected_before_interpreter():
    result, path = run_source('return 10\nrun("must not run")\n')
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "error: return outside function\n"
        f"  --> {path}:1:1\n"
    )


def test_return_inside_function_remains_valid():
    result, _ = run_source(
        "fn value() do\n"
        "    return 10\n"
        "end\n"
        "run(value())\n",
    )
    assert result.returncode == 0
    assert result.stdout == "10\n"
    assert result.stderr == ""
