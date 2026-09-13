#!/usr/bin/env python3
"""
Danilium 0.2 - CLI entry point.

Usage:
    python3 danilium.py hello.dnl     Run a Danilium source file
    python3 danilium.py               Start the Danilium REPL
"""

import sys

from lexer import Lexer, LexError, TokenType
from parser import Parser, ParseError
from type_checker import TypeChecker, DaniliumTypeError
from interpreter import Interpreter, DaniliumRuntimeError


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


def run_source(source: str):
    source_lines = source.splitlines()
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        TypeChecker(source_lines).check_program(program)
        Interpreter().run(program)
    except LexError as e:
        print(f"Lex error at line {e.line}: {e.message}")
        sys.exit(1)
    except ParseError as e:
        print(f"Syntax error at line {e.line}: {e.message}")
        sys.exit(1)
    except DaniliumTypeError as e:
        print(e.message)
        if e.source_line:
            print()
            print(f"    {e.source_line.strip()}")
        sys.exit(1)
    except DaniliumRuntimeError as e:
        print(f"Runtime error: {e}")
        sys.exit(1)


def run_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    run_source(source)


def repl():
    print("Danilium 0.2")
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
            print(f"Error: {e.message}")
        except DaniliumTypeError as e:
            print(e.message)
        except DaniliumRuntimeError as e:
            print(f"Runtime error: {e}")


def main():
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()


if __name__ == "__main__":
    main()
