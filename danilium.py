#!/usr/bin/env python3
"""
Danilium 0.3 - CLI entry point.

Usage:
    python3 danilium.py hello.dnl     Run a Danilium source file
    python3 danilium.py               Start the Danilium REPL
"""

import sys

from lexer import Lexer, LexError, TokenType
from parser import Parser, ParseError
from type_checker import TypeChecker, DaniliumTypeError
from interpreter import Interpreter, DaniliumRuntimeError
from diagnostics import from_exception


def _do_end_balance(line: str) -> int:
    """+1 per 'do' token, -1 per 'end' token on this line (0 if it doesn't lex)."""
    try:
        tokens = Lexer(line).tokenize()
    except LexError:
        return 0
    balance = 0
    for tok in tokens:
        if tok.type == TokenType.DO:
            balance += 1
        elif tok.type == TokenType.END:
            balance -= 1
    return balance


def report_diagnostic(error, filename):
    print(from_exception(error, filename).format(), file=sys.stderr)


def run_source(source: str, filename="<input>"):
    source_lines = source.splitlines()
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        TypeChecker(source_lines).check_program(program)
        Interpreter().run(program)
    except LexError as e:
        report_diagnostic(e, filename)
        return 1
    except ParseError as e:
        report_diagnostic(e, filename)
        return 1
    except DaniliumTypeError as e:
        report_diagnostic(e, filename)
        return 1
    except DaniliumRuntimeError as e:
        report_diagnostic(e, filename)
        return 1
    return 0


def run_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return run_source(source, path)


def repl():
    print("Danilium 0.3")
    print("Type an expression, or Ctrl+D / Ctrl+C to exit.")
    print()
    interp = Interpreter()
    checker = TypeChecker()
    buffer_lines = []
    open_blocks = 0
    while True:
        prompt = ">>> " if open_blocks == 0 else "... "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip() and open_blocks == 0:
            continue
        buffer_lines.append(line)
        open_blocks += _do_end_balance(line)
        if open_blocks > 0:
            continue  # keep collecting lines until every do/end is closed
        source = "\n".join(buffer_lines)
        buffer_lines = []
        open_blocks = 0
        try:
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse()
            checker.check_program(program)
            for stmt in program.statements:
                result = interp.execute(stmt)
                if result is not None:
                    print(result)
        except (LexError, ParseError) as e:
            report_diagnostic(e, "<repl>")
        except DaniliumTypeError as e:
            report_diagnostic(e, "<repl>")
        except DaniliumRuntimeError as e:
            report_diagnostic(e, "<repl>")


def main():
    if len(sys.argv) > 1:
        return run_file(sys.argv[1])
    else:
        repl()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
