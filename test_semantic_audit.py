"""Regression tests recording the observed Danilium 0.2 semantics.

These tests intentionally preserve current behavior, including known
checker/runtime inconsistencies. Language design changes belong in a later
version and should update these expectations explicitly.
"""

import contextlib
import io

import pytest

from interpreter import DaniliumRuntimeError, Interpreter
from lexer import Lexer
from parser import Parser
from type_checker import DaniliumTypeError, TypeChecker


def compile_source(source):
    program = Parser(Lexer(source).tokenize()).parse()
    checker = TypeChecker(source.splitlines())
    checker.check_program(program)
    return program, checker


def execute_source(source):
    program, checker = compile_source(source)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        Interpreter().run(program)
    return output.getvalue(), program, checker


def test_function_assignment_mutates_global_binding():
    output, _, _ = execute_source(
        "x = 10\n"
        "fn change() do\n"
        "    x = 20\n"
        "end\n"
        "change()\n"
        "run(x)\n"
    )
    assert output == "20\n"


@pytest.mark.parametrize("block", ["if true do\n    x = 10\nend", "while false do\n    x = 10\nend"])
def test_function_cannot_read_binding_declared_in_block(block):
    source = (
        f"{block}\n"
        "fn read_x() do\n"
        "    return x\n"
        "end\n"
        "run(read_x())\n"
    )
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="Undefined variable 'x'"):
        TypeChecker(source.splitlines()).check_program(program)


def test_call_before_function_declaration_is_rejected_by_type_checker():
    source = "square(5)\nfn square(x) do\n    return x * x\nend\n"
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="Unknown function 'square'"):
        TypeChecker(source.splitlines()).check_program(program)


def test_runtime_still_guards_return_outside_function():
    """The v0.2 runtime guard remains defense in depth after static checking."""
    source = "return 5\n"
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumRuntimeError, match="return.*outside of a function"):
        Interpreter().run(program)


def test_let_is_equivalent_to_assignment():
    let_output, _, _ = execute_source("let x = 10\nx = 20\nrun(x)\n")
    assignment_output, _, _ = execute_source("x = 10\nx = 20\nrun(x)\n")
    assert let_output == assignment_output == "20\n"


def test_let_binding_keeps_inferred_type_fixed():
    source = 'let x = 10\nx = "hello"\n'
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="x is int, but you assigned a string"):
        TypeChecker(source.splitlines()).check_program(program)


def test_not_bool_values_use_runtime_truthiness():
    output, _, _ = execute_source("run(not true)\nrun(not false)\nrun(not 0)\n")
    assert output == "False\nTrue\nTrue\n"


def test_any_return_value_is_allowed_as_condition_and_uses_truthiness():
    source = (
        "fn value() do\n"
        "    return 1\n"
        "end\n"
        "if value() do\n"
        '    run("yes")\n'
        "end\n"
    )
    output, _, _ = execute_source(source)
    assert output == "yes\n"


def test_integer_division_is_typed_int_but_evaluates_to_float():
    source = "x = 5 / 2\nrun(x)\n"
    output, program, checker = execute_source(source)
    assert checker.infer(program.statements[0].value) == "int"
    assert output == "2.5\n"


def test_function_declaration_is_not_a_variable_value():
    source = "fn square(x) do\n    return x * x\nend\nf = square\n"
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="Undefined variable 'square'"):
        TypeChecker(source.splitlines()).check_program(program)
