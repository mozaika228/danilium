"""
Danilium Semantic Analyzer - 0.3 rules.

Variables:
    - type is inferred at first assignment and then fixed
    - reassigning to an existing name must keep the same type
    - assignment mutates the nearest existing binding found by walking
      outward through enclosing scopes; if the name doesn't exist yet,
      it's declared in the current (innermost) scope

Scoping:
    - if/while blocks have their own scope (Variant A): a name first
      introduced inside a block disappears when the block ends
    - functions see the global scope (closures) plus their own
      parameters/locals - they do NOT see the caller's block-local
      variables

if/while:
    - the condition must be exactly `bool` (no truthiness on int/string)

Supported concrete types: 'int', 'float', 'string', 'bool'.
Function parameters without an explicit annotation are typed 'any' and
skip strict checking - full generic inference is future work.
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
    ListLiteral,
    IndexExpr,
    IndexAssignment,
    If,
    While,
    FnDecl,
    Return,
)

NUMERIC_TYPES = ("int", "float")
ANY = "any"

BUILTIN_FUNCTIONS = {
    "run": {"min_args": 1, "max_args": 1},
    "print": {"min_args": 1, "max_args": 1},
    "len": {"min_args": 1, "max_args": 1},
    "append": {"min_args": 2, "max_args": 2},
    "remove": {"min_args": 2, "max_args": 2},
}


class DaniliumTypeError(Exception):
    def __init__(self, message, line, source_line=None, column=1):
        super().__init__(message)
        self.message = message
        self.line = line
        self.source_line = source_line
        self.column = column


class TypeChecker:
    def __init__(self, source_lines=None):
        self.scopes = [{}]           # stack of {name: type}; index 0 = global
        self.functions = {}          # name -> FnDecl (for arg-count checks)
        self.source_lines = source_lines or []
        self.function_depth = 0

    # -- scope helpers --------------------------------------------------

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def declare(self, name, type_):
        self.scopes[-1][name] = type_

    def find_scope_with(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope
        return None

    def lookup(self, name):
        scope = self.find_scope_with(name)
        return scope[name] if scope is not None else None

    def _line_text(self, line):
        if 1 <= line <= len(self.source_lines):
            return self.source_lines[line - 1]
        return None

    def error(self, message, line, column=None):
        source_line = self._line_text(line)
        if column is None:
            column = len(source_line) - len(source_line.lstrip()) + 1 if source_line else 1
        raise DaniliumTypeError(message, line, source_line, column)

    # -- entry point ------------------------------------------------------

    def check_program(self, program):
        for stmt in program.statements:
            self.check_statement(stmt)

    def check_block(self, statements):
        for stmt in statements:
            self.check_statement(stmt)

    def check_statement(self, stmt):
        if isinstance(stmt, Assignment):
            self._check_assignment(stmt)
        elif isinstance(stmt, IndexAssignment):
            self._check_index_assignment(stmt)
        elif isinstance(stmt, If):
            self._check_if(stmt)
        elif isinstance(stmt, While):
            self._check_while(stmt)
        elif isinstance(stmt, FnDecl):
            self._check_fn(stmt)
        elif isinstance(stmt, Return):
            if self.function_depth == 0:
                self.error("return outside function", stmt.line)
            if stmt.value is not None:
                self.infer(stmt.value)
        elif isinstance(stmt, FunctionCall):
            self.check_call(stmt)
        else:
            self.infer(stmt)

    def _check_assignment(self, stmt):
        value_type = self.infer(stmt.value)
        target_type = value_type

        if stmt.type_annotation is not None:
            if stmt.type_annotation != value_type and value_type != ANY:
                self.error(
                    f"Type mismatch at line {stmt.line}\n\n"
                    f"{stmt.name} is declared as {stmt.type_annotation}, "
                    f"but you assigned a {value_type}.",
                    stmt.line,
                )
            target_type = stmt.type_annotation

        existing_scope = self.find_scope_with(stmt.name)
        if existing_scope is not None:
            existing_type = existing_scope[stmt.name]
            if existing_type != ANY and target_type != ANY and existing_type != target_type:
                self.error(
                    f"Type mismatch at line {stmt.line}\n\n"
                    f"{stmt.name} is {existing_type}, but you assigned a {target_type}.",
                    stmt.line,
                )
            if existing_type == ANY:
                existing_scope[stmt.name] = target_type
        else:
            self.declare(stmt.name, target_type)

    def _check_index_assignment(self, stmt):
        list_type = self.infer(stmt.collection)
        index_type = self.infer(stmt.index)
        value_type = self.infer(stmt.value)
        if index_type not in ("int", ANY):
            self.error(f"List index must be int, got {index_type}.", stmt.index.line)
        if not (list_type.startswith("list[") and list_type.endswith("]")):
            self.error(f"Cannot assign through index of type {list_type}.", stmt.line)
        element_type = list_type[5:-1]
        if value_type not in (element_type, ANY):
            self.error(
                f"Cannot assign {value_type} to {element_type} list element.",
                stmt.value.line,
            )

    def _require_bool(self, node, keyword):
        t = self.infer(node)
        if t not in ("bool", ANY):
            self.error(
                f"Type mismatch at line {node.line}\n\n"
                f"'{keyword}' expects a bool condition, but got {t}.",
                node.line,
            )

    def _check_if(self, stmt: If):
        self._require_bool(stmt.condition, "if")
        self.push_scope()
        self.check_block(stmt.then_block)
        self.pop_scope()

        for cond, body in stmt.elif_clauses:
            self._require_bool(cond, "elif")
            self.push_scope()
            self.check_block(body)
            self.pop_scope()

        if stmt.else_block is not None:
            self.push_scope()
            self.check_block(stmt.else_block)
            self.pop_scope()

    def _check_while(self, stmt: While):
        self._require_bool(stmt.condition, "while")
        self.push_scope()
        self.check_block(stmt.body)
        self.pop_scope()

    def _check_fn(self, stmt: FnDecl):
        self.functions[stmt.name] = stmt
        # Functions close over the global scope only - not whatever
        # block scopes happen to be active where they're defined.
        global_scope = self.scopes[0]
        saved_scopes = self.scopes
        self.scopes = [global_scope, {}]
        self.function_depth += 1
        try:
            for param_name, param_type in stmt.params:
                self.declare(param_name, param_type or ANY)
            self.check_block(stmt.body)
        finally:
            self.function_depth -= 1
            self.scopes = saved_scopes

    def check_call(self, node: FunctionCall):
        spec = BUILTIN_FUNCTIONS.get(node.name)
        if spec is not None:
            if not (spec["min_args"] <= len(node.args) <= spec["max_args"]):
                self.error(
                    f"'{node.name}' expects {spec['min_args']} argument(s) "
                    f"but got {len(node.args)} at line {node.line}",
                    node.line,
                )
            if node.name in ("len", "append", "remove"):
                return self._check_list_builtin(node)
            for arg in node.args:
                self.infer(arg)
            return "void"

        fn = self.functions.get(node.name)
        if fn is None:
            self.error(f"Unknown function '{node.name}' at line {node.line}", node.line)
        if len(node.args) != len(fn.params):
            self.error(
                f"'{node.name}' expects {len(fn.params)} argument(s) "
                f"but got {len(node.args)} at line {node.line}",
                node.line,
            )
        for arg in node.args:
            self.infer(arg)
        return ANY

    def _list_element_type(self, type_, line, operation):
        if not (type_.startswith("list[") and type_.endswith("]")):
            self.error(f"'{operation}' expects a list, got {type_}.", line)
        return type_[5:-1]

    def _check_list_builtin(self, node):
        list_type = self.infer(node.args[0])
        element_type = self._list_element_type(
            list_type, node.args[0].line, node.name
        )

        if node.name == "len":
            return "int"

        if node.name == "append":
            value_type = self.infer(node.args[1])
            if value_type not in (element_type, ANY):
                self.error(
                    f"Cannot append {value_type} to {element_type} list.",
                    node.args[1].line,
                )
            return "void"

        index_type = self.infer(node.args[1])
        if index_type not in ("int", ANY):
            self.error(f"List index must be int, got {index_type}.", node.args[1].line)
        return "void"

    # -- expression inference ----------------------------------------------

    def infer(self, node):
        if isinstance(node, StringLiteral):
            return "string"

        if isinstance(node, NumberLiteral):
            return "float" if isinstance(node.value, float) else "int"

        if isinstance(node, BooleanLiteral):
            return "bool"

        if isinstance(node, Identifier):
            found = self.lookup(node.name)
            if found is None:
                self.error(f"Undefined variable '{node.name}' at line {node.line}", node.line)
            return found

        if isinstance(node, ListLiteral):
            if not node.elements:
                self.error("Empty list literals are not supported", node.line)
            element_type = self.infer(node.elements[0])
            if element_type == ANY:
                self.error(
                    "List element type cannot be inferred from 'any' without "
                    "an explicit type annotation.",
                    node.elements[0].line,
                )
            for element in node.elements[1:]:
                current_type = self.infer(element)
                if current_type != element_type:
                    self.error(
                        "List elements must all have the same type "
                        f"(expected {element_type}, found {current_type}).",
                        element.line,
                    )
            return f"list[{element_type}]"

        if isinstance(node, IndexExpr):
            list_type = self.infer(node.collection)
            index_type = self.infer(node.index)
            if index_type not in ("int", ANY):
                self.error(
                    f"List index must be int, got {index_type}.", node.index.line
                )
            if not (list_type.startswith("list[") and list_type.endswith("]")):
                self.error(f"Cannot index value of type {list_type}.", node.line)
            return list_type[5:-1]

        if isinstance(node, UnaryOp):
            operand_type = self.infer(node.operand)
            if node.op == "not":
                return "bool"
            if operand_type not in NUMERIC_TYPES and operand_type != ANY:
                self.error(
                    f"Type mismatch at line {node.line}\n\n"
                    f"cannot use unary '-' on a {operand_type}.",
                    node.line,
                )
            return operand_type

        if isinstance(node, BinOp):
            return self._infer_binop(node)

        if isinstance(node, FunctionCall):
            return self.check_call(node)

        self.error(f"Cannot infer type of node {node}", getattr(node, "line", 0))

    def _infer_binop(self, node: BinOp):
        left_type = self.infer(node.left)
        right_type = self.infer(node.right)

        if node.op in ("and", "or"):
            self._require_operand_bool(node, "left", left_type)
            self._require_operand_bool(node, "right", right_type)
            return "bool"

        if node.op in ("==", "!="):
            return "bool"

        if node.op in ("<", ">", "<=", ">="):
            if ANY in (left_type, right_type):
                return "bool"
            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                self.error(
                    f"Type mismatch at line {node.line}\n\n"
                    f"cannot compare {left_type} and {right_type} with '{node.op}'.",
                    node.line,
                )
            return "bool"

        if node.op == "+":
            if ANY in (left_type, right_type):
                return ANY
            if left_type == "string" or right_type == "string":
                if left_type != right_type:
                    self.error(
                        f"Type mismatch at line {node.line}\n\n"
                        f"cannot use '+' between {left_type} and {right_type}.",
                        node.line,
                    )
                return "string"
            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                self.error(
                    f"Type mismatch at line {node.line}\n\n"
                    f"cannot use '+' between {left_type} and {right_type}.",
                    node.line,
                )
            return "float" if "float" in (left_type, right_type) else "int"

        # - * /
        if ANY in (left_type, right_type):
            return ANY
        if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
            self.error(
                f"Type mismatch at line {node.line}\n\n"
                f"cannot use '{node.op}' between {left_type} and {right_type}.",
                node.line,
            )
        return "float" if "float" in (left_type, right_type) else "int"

    def _require_operand_bool(self, node, side, type_):
        if type_ not in ("bool", ANY):
            self.error(
                f"Type mismatch at line {node.line}\n\n"
                f"'{node.op}' expects bool operands, but the {side} side is {type_}.",
                node.line,
            )
