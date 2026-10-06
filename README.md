# Danilium

<div align="center">

<img src="assets/danilium-logo.jpeg" alt="Danilium logo" width="420" />

**SIMPLE • FLEXIBLE • POWERFUL**

**A programming language built from scratch.**

</div>

Danilium is a small general-purpose programming language with its own lexer,
parser, AST, type checker, and tree-walk interpreter. The project makes
language design decisions explicit and testable.

## Quick Start

```bash
git clone https://github.com/mozaika228/danilium.git
cd danilium
python danilium.py hello.dnl
```

Output:

```text
Hello, Danilium
```

Use `python3` instead of `python` when that is how Python 3 is installed. To
open the REPL:

```bash
python danilium.py
```

The REPL supports multi-line `do ... end` blocks.

## Why Danilium?

Danilium is an experiment in building a language from first principles:

- its lexer, parser, AST, type checker, and interpreter are part of the project;
- variable types are inferred on first assignment and then checked;
- blocks have explicit `do ... end` boundaries and lexical scopes;
- list behavior, diagnostics, and other semantics are recorded in tests and
  specifications;
- programs are parsed and interpreted directly, without Python `eval()` or a
  parser generator.

The goal is a low floor and a high ceiling: Danilium should be easy to start
with without being limited to simple programs.

The language is being developed from semantics outward: rules are specified,
tested, and implemented before new layers are added. This gives the project a
clear path from the current interpreter toward a richer type system, IR, and VM.

## Language

### Variables and types

Types are inferred at first assignment and remain fixed:

```danilium
name = "Danilium"
version = 3
active = true
```

`let` is currently optional assignment syntax:

```danilium
let count = 1
count = 2
```

### Expressions, conditions, and loops

```danilium
x = 10
x += 2

if x > 10 and not false do
    run("ready")
end

while x < 15 do
    x += 1
end
```

Danilium supports arithmetic, comparisons, `and`, `or`, `not`, and compound
assignment (`+=`, `-=`, `*=`, `/=`).

### Functions

```danilium
fn square(value) do
    return value * value
end

run(square(5))
```

Named functions and direct calls are supported. Function parameters do not yet
have explicit type annotations, and functions are not first-class values.

### Lists

Danilium 0.3 supports non-empty homogeneous mutable lists:

```danilium
numbers = [10, 20, 30]
numbers[1] = 99
append(numbers, 40)
remove(numbers, 0)
run(len(numbers))
```

List indexes are zero-based. Invalid indexes produce a runtime diagnostic;
mixed or empty list literals are rejected by the type checker. List assignment
uses reference semantics, so aliases observe the same mutations.

### Scopes and diagnostics

`if`, `while`, and function bodies have explicit scope behavior documented in
the semantic audit. Lexing, parsing, type, and runtime failures use a common
diagnostic format and are written to standard error; `run(...)` writes to
standard output.

## Examples

The repository contains runnable programs:

| File | Demonstrates |
| --- | --- |
| [`hello.dnl`](hello.dnl) | strings, conditions, functions, and loops |
| [`hello_world.dnl`](hello_world.dnl) | the smallest hello-world program |
| [`lists.dnl`](lists.dnl) | list indexing, mutation, and built-ins |
| [`conditions.dnl`](conditions.dnl) | conditional branches |
| [`loop.dnl`](loop.dnl) | a while loop |
| [`functions.dnl`](functions.dnl) | named functions and global access |
| [`scoping.dnl`](scoping.dnl) | block-scope diagnostics |

The first six examples run successfully. `scoping.dnl` intentionally
demonstrates an undefined-variable diagnostic.

## Architecture

```text
Danilium source
      ↓
    Lexer
      ↓
    Parser
      ↓
     AST
      ↓
 Type Checker
      ↓
 Interpreter
      ↓
    Output
```

The core implementation is split across [`lexer.py`](lexer.py),
[`parser.py`](parser.py), [`ast_nodes.py`](ast_nodes.py),
[`type_checker.py`](type_checker.py), [`interpreter.py`](interpreter.py), and
[`danilium.py`](danilium.py).

## Current Status

### Implemented

- own lexer and parser;
- AST and tree-walk interpreter;
- inferred, fixed variable types;
- variables, assignment, expressions, and logical operators;
- `if`, `elif`, `else`, and `while`;
- named functions and return values;
- block scopes and semantic regression tests;
- homogeneous lists, indexing, mutation, aliasing, `len`, `append`, and
  `remove`;
- unified CLI diagnostics and static validation of `return` outside functions;
- REPL and basic VS Code syntax support for `.dnl` files.

### Under development

- typed function signatures and return annotations;
- first-class functions and lexical closures;
- modules and imports;
- richer collection types and explicit type annotations;
- `Option` / `Result` style error handling;
- Danilium IR, bytecode, and a VM;
- native compilation.

## Roadmap

| Release | Focus |
| --- | --- |
| 0.3 | language foundations, lists, diagnostics, and semantic tests |
| 0.4 | structs, enums, and a standard collection foundation |
| 0.5 | modules, imports, and library organization |
| 0.6+ | IR, bytecode VM, generics, and further runtime work |

The roadmap is subject to the language specification and test suite. Features
are added after their semantics are defined.

## Language Design

- [`docs/SPEC_V0_3.md`](docs/SPEC_V0_3.md) — v0.3 release scope;
- [`docs/SEMANTIC_AUDIT_V0_2.md`](docs/SEMANTIC_AUDIT_V0_2.md) — observed v0.2
  behavior and regression baseline.

## Development

```bash
python -m pip install -r requirements-dev.txt
pytest -v
```

The VS Code extension source is in [`danilium-vscode`](danilium-vscode). To
try it from a checkout:

```bash
code --extensionDevelopmentPath=./danilium-vscode .
```

Good contribution ideas include semantic tests, documentation fixes,
lexer/parser improvements, and small issues labeled `good first issue`.

## License

Danilium is released under the [MIT License](LICENSE).
