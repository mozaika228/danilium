# Danilium

Danilium is a programming language designed around simple, readable syntax and a clear language architecture.

## Syntax

```danilium
# comments start with #

x = 10

if x > 5 -> run("big")

if x >= 90 do
    run("Ancient")
elif x >= 18 do
    run("Adult")
else
    run("Minor")
end

while x < 20 do
    x += 1
end

fn square(n) do
    return n * n
end

run(square(5))
```

* Blocks use `do ... end`.
* `->` provides a single-statement form.
* `elif` is used instead of `else if`.
* Comparisons: `== != < > <= >=`.
* Logic: `and or not`.
* Conditions must evaluate to `bool`.
* Compound assignment: `+= -= *= /=`.
* `let` is optional syntax before an assignment (`let x = 10` is equivalent to `x = 10`).

## Language Rules

### Variables

A variable's type is inferred at first assignment and then fixed.

```danilium
age = 20
age = 21       # valid
age = "hello"  # type error
```

Assignment mutates the nearest existing binding found by walking outward through enclosing scopes. If the name does not exist, it is declared in the current scope.

### Scoping

`if` and `while` blocks have their own scope. A variable first introduced inside a block is not available after the block ends.

Assignment can still modify an existing variable from an outer scope:

```danilium
x = 10

while x < 20 do
    x += 1
end
```

Functions close over the global scope. They can read global variables, but do not capture block-local variables from the call site.

### Conditions

Conditions must evaluate exactly to `bool`.

There is no Python-style truthiness:

```danilium
if 10 do
    run("true")
end
```

This produces a type error rather than treating `10` as `true`.

## Architecture

The current Danilium execution pipeline is:

```text
Danilium source code
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

The implementation has its own lexer, parser, AST, type checker and interpreter. Danilium programs are not executed through Python's `eval()`.

## Project Structure

```text
danilium/
├── danilium.py
├── lexer.py
├── parser.py
├── ast_nodes.py
├── type_checker.py
├── interpreter.py
├── examples/
├── tests/
├── requirements-dev.txt
└── README.md
```

## Running Danilium

Clone the repository:

```bash
git clone https://github.com/mozaika228/danilium.git
cd danilium
```

Run an example:

```bash
python3 danilium.py examples/hello_world.dnl
python3 danilium.py examples/conditions.dnl
python3 danilium.py examples/loop.dnl
python3 danilium.py examples/functions.dnl
```

Run the REPL:

```bash
python3 danilium.py
```

The REPL supports multi-line `do ... end` blocks.

## Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest -v
```

The test suite covers example programs, control flow, functions, scoping and fixed variable types.

GitHub Actions runs the test suite on pushes and pull requests to `main`.

## Current Status

Danilium is currently in active development.

The current implementation provides:

* Lexer
* Parser
* Abstract Syntax Tree (AST)
* Type checker
* Tree-walk interpreter
* Variables and fixed types
* Control flow
* Functions
* Scoping rules
* Closures over the global scope
* Compound assignment
* Multi-line and single-line block syntax
* REPL

## Project Structure

| File              | Stage             | Role                                |
| ----------------- | ----------------- | ----------------------------------- |
| `lexer.py`        | Lexer             | Source text → tokens                |
| `ast_nodes.py`    | AST               | AST node definitions                |
| `parser.py`       | Parser            | Tokens → AST                        |
| `type_checker.py` | Semantic Analyzer | Type and scope checking             |
| `interpreter.py`  | Interpreter       | Executes the AST                    |
| `danilium.py`     | CLI               | Runs programs and provides the REPL |

## Known Limitations

Some language features are not implemented yet, including:

* Fully typed function parameters
* Function hoisting
* Structs and enums
* Collections
* Modules
* Dedicated error-handling types such as `Result` and `Option`
* A dedicated IR / VM backend
* Native compilation

## Roadmap

Danilium is being developed incrementally.

Current areas of development include:

* Language syntax
* Type system
* Functions
* Collections
* Control flow
* Modules
* Standard library
* Runtime architecture
* Performance

The roadmap may change as the language evolves.

## Long-Term Vision

Danilium is built around a simple idea:

> **Make programming easy to learn without limiting what developers can build.**

The language starts with readable syntax and a small core, while leaving room for deeper programming concepts and more advanced software.

Danilium starts simple.

The rest is built step by step.

**Simple to learn. Flexible to use. Powerful to build.**

