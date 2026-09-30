"""Initial v0.3 list literal and read-indexing tests."""

import contextlib
import io

import pytest

from interpreter import DaniliumRuntimeError, Interpreter
from lexer import Lexer
from parser import ParseError, Parser
from type_checker import DaniliumTypeError, TypeChecker


def parse_and_check(source):
    program = Parser(Lexer(source).tokenize()).parse()
    TypeChecker(source.splitlines()).check_program(program)
    return program


def run_source(source):
    program = parse_and_check(source)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        Interpreter().run(program)
    return output.getvalue()


def test_list_literal_and_zero_based_read_indexing():
    assert run_source(
        "numbers = [10, 20, 30]\n"
        "run(numbers[0])\n"
        "run(numbers[2])\n"
    ) == "10\n30\n"


def test_string_list_indexing():
    assert run_source('names = ["Alice", "Bob"]\nrun(names[1])\n') == "Bob\n"


def test_mixed_list_literal_is_a_type_error():
    source = 'values = [1, "hello", 3]\n'
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="List elements must all have the same type"):
        TypeChecker(source.splitlines()).check_program(program)


def test_any_elements_need_explicit_annotation_before_list_inference():
    source = (
        "fn first() do\n"
        "    return 1\n"
        "end\n"
        "fn second() do\n"
        '    return "two"\n'
        "end\n"
        "values = [first(), second()]\n"
    )
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="cannot be inferred from 'any'"):
        TypeChecker(source.splitlines()).check_program(program)


def test_empty_list_literal_is_rejected():
    with pytest.raises(DaniliumTypeError, match="Empty list literals are not supported"):
        parse_and_check("values = []\n")


def test_index_must_be_an_integer():
    source = 'names = ["Alice"]\nrun(names["0"])\n'
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="List index must be int"):
        TypeChecker(source.splitlines()).check_program(program)


@pytest.mark.parametrize("index", [3, -1])
def test_out_of_bounds_and_negative_indexes_raise_runtime_error(index):
    program = parse_and_check(f"numbers = [10, 20, 30]\nrun(numbers[{index}])\n")
    with pytest.raises(DaniliumRuntimeError, match="List index out of bounds"):
        Interpreter().run(program)


def test_list_assignment_preserves_reference_aliasing():
    source = "a = [1, 2]\nb = a\n"
    program = parse_and_check(source)
    interpreter = Interpreter()
    interpreter.run(program)
    assert interpreter.lookup_var("a") is interpreter.lookup_var("b")


def test_index_assignment_updates_existing_element():
    assert run_source(
        "numbers = [10, 20, 30]\n"
        "numbers[1] = 99\n"
        "run(numbers[1])\n"
    ) == "99\n"


def test_index_assignment_rejects_incompatible_element_type():
    source = 'numbers = [10, 20, 30]\nnumbers[1] = "hello"\n'
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="Cannot assign string to int list element"):
        TypeChecker(source.splitlines()).check_program(program)


@pytest.mark.parametrize("index", [10, -1])
def test_index_assignment_out_of_bounds_does_not_mutate_list(index):
    source = f"numbers = [10, 20, 30]\nnumbers[{index}] = 50\n"
    program = parse_and_check(source)
    interpreter = Interpreter()
    with pytest.raises(DaniliumRuntimeError, match="List index out of bounds"):
        interpreter.run(program)
    assert interpreter.lookup_var("numbers") == [10, 20, 30]


def test_dynamic_assignment_type_error_does_not_mutate_list():
    source = (
        "numbers = [10, 20, 30]\n"
        "fn replace(value) do\n"
        "    numbers[1] = value\n"
        "end\n"
        'replace("hello")\n'
    )
    program = parse_and_check(source)
    interpreter = Interpreter()
    with pytest.raises(DaniliumRuntimeError, match="does not match list element type"):
        interpreter.run(program)
    assert interpreter.lookup_var("numbers") == [10, 20, 30]


def test_len_returns_list_length_and_has_int_type():
    source = "numbers = [10, 20, 30]\nsize = len(numbers)\nrun(size)\n"
    program = Parser(Lexer(source).tokenize()).parse()
    checker = TypeChecker(source.splitlines())
    checker.check_program(program)
    assert checker.lookup("size") == "int"
    assert run_source(source) == "3\n"


def test_len_rejects_non_list_argument():
    source = "len(10)\n"
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="'len' expects a list"):
        TypeChecker(source.splitlines()).check_program(program)


def test_append_mutates_list_and_updates_length():
    source = (
        "numbers = [10, 20]\n"
        "append(numbers, 30)\n"
        "run(numbers[2])\n"
        "run(len(numbers))\n"
    )
    assert run_source(source) == "30\n3\n"


def test_append_rejects_incompatible_type_before_runtime():
    source = 'numbers = [1, 2]\nappend(numbers, "x")\n'
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="Cannot append string to int list"):
        TypeChecker(source.splitlines()).check_program(program)


def test_dynamic_append_type_error_leaves_list_unchanged():
    source = (
        "numbers = [1, 2]\n"
        "fn add(value) do\n"
        "    append(numbers, value)\n"
        "end\n"
        'add("x")\n'
    )
    program = parse_and_check(source)
    interpreter = Interpreter()
    with pytest.raises(DaniliumRuntimeError, match="does not match list element type"):
        interpreter.run(program)
    assert interpreter.lookup_var("numbers") == [1, 2]


def test_append_works_after_removing_last_element():
    assert run_source(
        "numbers = [1]\n"
        "remove(numbers, 0)\n"
        "append(numbers, 2)\n"
        "run(numbers[0])\n"
    ) == "2\n"


def test_remove_mutates_list_and_returns_void():
    source = "numbers = [10, 20, 30]\nremove(numbers, 1)\nrun(numbers[1])\n"
    program = parse_and_check(source)
    interpreter = Interpreter()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        interpreter.run(program)
    assert output.getvalue() == "30\n"
    assert interpreter.evaluate(program.statements[1]) is None


@pytest.mark.parametrize("index", [-1, 2])
def test_remove_invalid_index_raises_bounds_error_without_mutation(index):
    source = f"numbers = [10, 20]\nremove(numbers, {index})\n"
    program = parse_and_check(source)
    interpreter = Interpreter()
    with pytest.raises(DaniliumRuntimeError, match="List index out of bounds"):
        interpreter.run(program)
    assert interpreter.lookup_var("numbers") == [10, 20]


def test_remove_rejects_non_integer_index():
    source = 'numbers = [10, 20]\nremove(numbers, "x")\n'
    program = Parser(Lexer(source).tokenize()).parse()
    with pytest.raises(DaniliumTypeError, match="List index must be int"):
        TypeChecker(source.splitlines()).check_program(program)
