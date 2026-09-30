# Danilium v0.3 Language Specification (Draft)

**Status:** implemented release-candidate scope.

This document defines the deliberately small v0.3.0 release. It is informed by
the behavior recorded in [`SEMANTIC_AUDIT_V0_2.md`](SEMANTIC_AUDIT_V0_2.md).
The audit is the historical record of v0.2; this draft describes proposed
changes and must not be read as retroactively changing v0.2.

## 1. Release goal

Danilium v0.3.0 adds mutable homogeneous lists, list indexing and mutation, and
a consistent user-facing diagnostic contract. It also moves invalid `return`
outside a function from runtime to type-check time. Modules and
functions-as-values are not part of v0.3.0; they require separate design
decisions before implementation.

The rules below define the v0.3.0 contract and are covered by the implementation
and regression tests.

## 2. Lists

### 2.1 Literal and element type

List literals use square brackets, with comma-separated expressions:

```danilium
numbers = [1, 2, 3]
```

The v0.3.0 rule is that lists are homogeneous by default. A non-empty literal
infers its element type from its first element; every later element must have
the same type. Thus `[1, 2]` is valid and `[1, "two"]` is a type error.

Heterogeneous lists are not allowed by default. The `any` type may permit
heterogeneous elements once Danilium defines syntax for explicit type
annotations. Such syntax is not introduced solely for lists in v0.3.0, so a
form such as `values: any = [1, "hello", true]` is not part of this release.

Empty list literals (`[]`) are rejected in v0.3.0 because this draft does not
yet define generic type annotations such as `List<int>`. Nested lists are
deferred until their type syntax and mutation rules are specified.

### 2.2 Indexing

Indexes are zero-based integer expressions:

```danilium
run(numbers[0])
```

The index expression must have type `int`. Reading an index outside the range
`0 .. len(list)-1` raises a runtime bounds diagnostic. Negative indexes are
not supported in v0.3.0; `numbers[-1]` raises the same runtime bounds
diagnostic as `numbers[10]` on a shorter list. Negative indexes do not count
from the end.

### 2.3 Mutation

An indexed assignment replaces an existing element:

```danilium
numbers[2] = 10
```

The replacement value must match the list's element type. A different type is
a type error. The index must identify an existing element in the range
`0 .. len(list)-1`; an out-of-range indexed assignment raises a runtime bounds
diagnostic. It does not grow the list or fill gaps.

The v0.3.0 list built-ins are:

```danilium
append(numbers, 6)       # add one element at the end
remove(numbers, 0)       # remove the element at index 0
length = len(numbers)    # number of elements
```

`append` accepts a value matching the element type and returns `void`.
`remove` requires an integer index and returns `void`; it mutates the list
without returning the removed element. `len` accepts a list and returns `int`.
Removing an invalid index raises the same runtime bounds diagnostic as
indexing.

### 2.4 Mutability and assignment

Lists are mutable and have reference semantics. Assigning a list to another
variable copies the reference, not the list elements; mutations through
either variable are visible through the other. For example, after `b = a`,
`b[0] = 99` also changes the first element observed through `a`. Rebinding a
variable follows the v0.2 assignment rule:
update the nearest existing binding, or declare in the current scope if none
exists.

The homogeneous element type remains fixed after construction. Indexed writes
and `append` with a different type are rejected during type checking.

## 3. Diagnostics and errors

### 3.1 Error categories

The implementation classifies failures in four categories:

| Category | When it occurs |
|---|---|
| `LexError` | Invalid character, malformed token, or unterminated literal. |
| `ParseError` | Tokens do not form a valid Danilium program. |
| `TypeError` | A name, type, arity, return, or collection rule fails static checking. |
| `RuntimeError` | A failure remains possible after static checking, such as division by zero or an invalid list index. |

Undefined variables and unknown functions are static `TypeError`s when the
checker can identify them. `return` outside a function is a static `TypeError`
in v0.3.0. The interpreter must not run if lexing, parsing, or type checking
fails.

These are diagnostic categories, not Danilium values or catchable exceptions.
An exception-handling language feature is outside this release.

### 3.2 Diagnostic presentation

The user-facing format is:

```text
error: <message>
  --> <file>:<line>:<column>
```

Line and column numbers are one-based. For example:

```text
error: list index out of bounds
  --> example.dnl:4:7
```

Diagnostics are written to standard error. Output from `run(...)` remains on
standard output. The CLI exits with status 0 on success and non-zero on a
diagnostic. Error origin is classified as lexer, parser, type checker, or
runtime internally; stable public error codes and caret spans are not required
by this v0.3.0 format.

## 4. Functions in v0.3.0

Named function declarations and direct calls remain supported. Function
parameters may still omit annotations in v0.3.0; complete parameter and return
type declarations are deferred. The existing return-value behavior remains:
a function can return a value, and a function with no executed `return` yields
`void`.

The type checker must reject `return` outside a function. Function declarations
are not first-class values: assigning a function name to a variable and
calling through that variable remain unsupported. Lexical closures are also
deferred. These are separate future design decisions, not implicit additions
to this release.

## 5. Modules and non-goals

Modules and `import` are deferred from v0.3.0. The following are also outside
the release: maps, structs, enums, generics, async/concurrency, package
management, IR/VM, native compilation, and exception handling in Danilium
programs.

## 6. Compatibility and tests

The v0.2 audit tests remain the record of observed v0.2 behavior. Tests for
v0.3 must encode the proposed rules above. Where a v0.3 rule intentionally
changes observed behavior—such as rejecting `return` during type checking—the
test change must be accompanied by this specification's corresponding rule.

At minimum, v0.3 tests cover:

- valid homogeneous lists and rejection of mixed or empty literals;
- zero-based reads, indexed writes, type mismatch, and bounds failures for
  both reads and writes; an out-of-range write must not extend the list;
- `append`, `remove`, and `len`, including invalid argument types and indexes;
- list aliasing and mutations through aliases;
- diagnostic message/location format, stderr vs stdout, and exit status;
- static rejection of `return` outside a function;
- unchanged v0.2 baseline behavior for rules not deliberately changed here.

## 7. Release status

The v0.3.0 scope is implemented as a release candidate: homogeneous non-empty
lists, indexing and indexed assignment, mutable reference aliasing, `len`,
`append`, `remove`, shared CLI diagnostics, and static validation of `return`
outside functions. Modules, function values, and closures remain deferred.
