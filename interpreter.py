"""
Danilium Interpreter - 0.2 runtime.

Mirrors the scoping rules enforced by the type checker:
    - assignment mutates the nearest existing binding, or declares a new
      one in the current (innermost) scope
    - if/while blocks push their own scope, popped when the block ends
    - functions run against [global_scope, local_scope] only - they close
      over globals but not over the caller's block-local variables
"""

from ast_nodes import (
    Assignment,
    FunctionCall,
    BinOp,
    UnaryOp,
    StringLiteral,
    NumberLiteral,
    BooleanLiteral,
    Identifier,
    If,
    While,
    FnDecl,
    Return,
)


class DaniliumRuntimeError(Exception):
    pass


class ReturnSignal(Exception):
    """Internal control-flow signal for `return` - never escapes run()."""

    def __init__(self, value):
        self.value = value


class Interpreter:
    def __init__(self):
        self.scopes = [{}]     # stack of {name: value}; index 0 = global
        self.functions = {}    # name -> FnDecl

    # -- scope helpers --------------------------------------------------

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def find_scope_with(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope
        return None

    def lookup_var(self, name):
        scope = self.find_scope_with(name)
        if scope is None:
            raise DaniliumRuntimeError(f"Undefined variable '{name}'")
        return scope[name]

    # -- entry point ------------------------------------------------------

    def run(self, program):
        try:
            for stmt in program.statements:
                self.execute(stmt)
        except ReturnSignal:
            raise DaniliumRuntimeError("'return' used outside of a function")

    def execute_block(self, statements):
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt):
        if isinstance(stmt, Assignment):
            value = self.evaluate(stmt.value)
            scope = self.find_scope_with(stmt.name)
            if scope is None:
                scope = self.scopes[-1]
            scope[stmt.name] = value
            return None

        if isinstance(stmt, If):
            return self._execute_if(stmt)

        if isinstance(stmt, While):
            return self._execute_while(stmt)

        if isinstance(stmt, FnDecl):
            self.functions[stmt.name] = stmt
            return None

        if isinstance(stmt, Return):
            value = self.evaluate(stmt.value) if stmt.value is not None else None
            raise ReturnSignal(value)

        return self.evaluate(stmt)

    def _execute_if(self, stmt: If):
        if self.truthy(self.evaluate(stmt.condition)):
            self.push_scope()
            try:
                self.execute_block(stmt.then_block)
            finally:
                self.pop_scope()
            return

        for cond, body in stmt.elif_clauses:
            if self.truthy(self.evaluate(cond)):
                self.push_scope()
                try:
                    self.execute_block(body)
                finally:
                    self.pop_scope()
                return

        if stmt.else_block is not None:
            self.push_scope()
            try:
                self.execute_block(stmt.else_block)
            finally:
                self.pop_scope()

    def _execute_while(self, stmt: While):
        while self.truthy(self.evaluate(stmt.condition)):
            self.push_scope()
            try:
                self.execute_block(stmt.body)
            finally:
                self.pop_scope()

    # -- expressions ------------------------------------------------------

    def truthy(self, value):
        return bool(value)

    def evaluate(self, node):
        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, NumberLiteral):
            return node.value

        if isinstance(node, BooleanLiteral):
            return node.value

        if isinstance(node, Identifier):
            return self.lookup_var(node.name)

        if isinstance(node, UnaryOp):
            value = self.evaluate(node.operand)
            if node.op == "not":
                return not self.truthy(value)
            if node.op == "-":
                return -value
            raise DaniliumRuntimeError(f"Unknown unary operator {node.op}")

        if isinstance(node, BinOp):
            return self._evaluate_binop(node)

        if isinstance(node, FunctionCall):
            return self.call_function(node)

        raise DaniliumRuntimeError(f"Cannot evaluate node {node}")

    def _evaluate_binop(self, node: BinOp):
        if node.op == "and":
            left = self.evaluate(node.left)
            if not self.truthy(left):
                return False
            return self.truthy(self.evaluate(node.right))

        if node.op == "or":
            left = self.evaluate(node.left)
            if self.truthy(left):
                return True
            return self.truthy(self.evaluate(node.right))

        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        if node.op == "<":
            return left < right
        if node.op == ">":
            return left > right
        if node.op == "<=":
            return left <= right
        if node.op == ">=":
            return left >= right

        raise DaniliumRuntimeError(f"Unknown operator {node.op}")

    def call_function(self, node: FunctionCall):
        if node.name in ("run", "print"):
            value = self.evaluate(node.args[0])
            print(value)
            return None

        fn = self.functions.get(node.name)
        if fn is None:
            raise DaniliumRuntimeError(f"Unknown function '{node.name}'")
        if len(node.args) != len(fn.params):
            raise DaniliumRuntimeError(
                f"'{node.name}' expects {len(fn.params)} argument(s) "
                f"but got {len(node.args)}"
            )

        arg_values = [self.evaluate(a) for a in node.args]
        local_scope = {}
        for (param_name, _), value in zip(fn.params, arg_values):
            local_scope[param_name] = value

        # Functions run against [global, local] only: they close over
        # globals, not over whatever block scope they were called from.
        saved_scopes = self.scopes
        self.scopes = [self.scopes[0], local_scope]
        try:
            self.execute_block(fn.body)
            return None
        except ReturnSignal as r:
            return r.value
        finally:
            self.scopes = saved_scopes
