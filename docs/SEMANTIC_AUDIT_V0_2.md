# Danilium v0.2 Semantic Audit

This document records behavior observed in the current v0.2 implementation and
the corresponding regression tests. It is an audit baseline, not a v0.3
specification. Every v0.3 decision remains open until explicitly accepted.

The observations below were reproduced with the lexer, parser, type checker,
and interpreter. The audit regression suite passed 11 tests.

## Observed behavior and open decisions

| ID | Topic | Observed in v0.2 | v0.3 decision | Regression test |
|---|---|---|---|---|
| AUDIT-001 | Assignment inside a function | Assignment to an existing global binding updates that binding. The example prints `20`. | Preserved in v0.3.0. | `test_function_assignment_mutates_global_binding` |
| AUDIT-002 | Function access to `if` locals | A function cannot resolve a variable first declared in an `if` block; type checking reports an undefined variable. | Preserved in v0.3.0. | `test_function_cannot_read_binding_declared_in_block` |
| AUDIT-003 | Function access to `while` locals | A function cannot resolve a variable first declared in a `while` block; type checking reports an undefined variable. | Preserved in v0.3.0. | `test_function_cannot_read_binding_declared_in_block` |
| AUDIT-004 | Calling before declaration | A call before the function declaration is rejected by the type checker as an unknown function. | Preserved in v0.3.0. | `test_call_before_function_declaration_is_rejected_by_type_checker` |
| AUDIT-005 | `return` outside a function | In v0.2, type checking accepted it and execution raised a runtime error. | Changed in v0.3.0: type checker rejects it; interpreter retains a defensive runtime guard. | `test_return_outside_function_is_rejected_before_interpreter`; `test_runtime_still_guards_return_outside_function` |
| AUDIT-006 | Meaning of `let` | `let x = value` is parsed as ordinary assignment; the demonstrated program behaves identically without `let`. | Preserved in v0.3.0. | `test_let_is_equivalent_to_assignment` |
| AUDIT-007 | Type stability after `let` | After `let x = 10`, assigning a string to `x` is rejected as a type mismatch. | Preserved in v0.3.0. | `test_let_binding_keeps_inferred_type_fixed` |
| AUDIT-008 | `not` and runtime truthiness | `not true` and `not false` work. `not 0` is also accepted and evaluates using runtime truthiness. | Preserved in v0.3.0. | `test_not_bool_values_use_runtime_truthiness` |
| AUDIT-009 | `any` in a condition | A function call whose inferred result is `any` is accepted as a condition; the runtime applies truthiness to its value. | Preserved in v0.3.0. | `test_any_return_value_is_allowed_as_condition_and_uses_truthiness` |
| AUDIT-010 | Integer division | The type checker infers `int` for `5 / 2`, while the interpreter produces `2.5` (a Python `float`). | Unchanged in v0.3.0; resolution deferred. | `test_integer_division_is_typed_int_but_evaluates_to_float` |
| AUDIT-011 | Functions as values | A declared function cannot be used as a variable value; `f = square` is rejected as an undefined variable. | Deferred; functions remain declarations, not values, in v0.3.0. | `test_function_declaration_is_not_a_variable_value` |

## Follow-up design questions

These questions remain for a later release:

1. Is `let` only an alias for assignment, or does it declare a new binding?
2. When does assignment create a binding, and when does it update an outer one?
3. If lexical closures are added, do they capture bindings by reference or by value?
4. Should functions be first-class values? This is separate from deciding whether
   nested functions capture lexical environments.
5. Should conditions and `not` require `bool`, or use runtime truthiness?
6. What type and value should division of two integers produce?
7. Which additional runtime and type errors should be caught statically?

## Change policy

The tests record current behavior; they do not declare every behavior desirable.
If a v0.3 decision changes one of these observations, update the relevant
specification and test expectation together and record the reason for the
semantic change.
