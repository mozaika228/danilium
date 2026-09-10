"""
Danilium Semantic Analyzer.

A minimal static type checker with inference, in the spirit of:

    age = 20            # inferred as int
    age: int = 20        # explicit, checked against the inferred type

Supported types in 0.1: 'int', 'float', 'string'.
"""

from ast_nodes import Assignment, FunctionCall, BinOp, StringLiteral, NumberLiteral, Identifier


class DaniliumTypeError(Exception):
    def __init__(self, message, line, source_line=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.source_line = source_line


BUILTIN_FUNCTIONS = {
    "run": {"min_args": 1, "max_args": 1},
}


class TypeChecker:
    def __init__(self, source_lines=None):
        self.symbols = {}  # name -> inferred/declared type
        self.source_lines = source_lines or []

    def _line_text(self, line):
        if 1 <= line <= len(self.source_lines):
            return self.source_lines[line - 1]
        return None

    def check_program(self, program):
        for stmt in program.statements:
            self.check_statement(stmt)

    def check_statement(self, stmt):
        if isinstance(stmt, Assignment):
            value_type = self.infer(stmt.value)
            if stmt.type_annotation is not None:
                if stmt.type_annotation != value_type:
                    raise DaniliumTypeError(
                        f"Type mismatch at line {stmt.line}\n\n"
                        f"{stmt.name} is declared as {stmt.type_annotation}, "
                        f"but you assigned a {value_type}.",
                        stmt.line,
                        self._line_text(stmt.line),
                    )
                self.symbols[stmt.name] = stmt.type_annotation
            else:
                self.symbols[stmt.name] = value_type
        elif isinstance(stmt, FunctionCall):
            self.check_call(stmt)
        else:
            self.infer(stmt)

    def check_call(self, node: FunctionCall):
        spec = BUILTIN_FUNCTIONS.get(node.name)
        if spec is None:
            raise DaniliumTypeError(
                f"Unknown function '{node.name}' at line {node.line}",
                node.line,
                self._line_text(node.line),
            )
        if not (spec["min_args"] <= len(node.args) <= spec["max_args"]):
            raise DaniliumTypeError(
                f"'{node.name}' expects {spec['min_args']} argument(s) "
                f"but got {len(node.args)} at line {node.line}",
                node.line,
                self._line_text(node.line),
            )
        for arg in node.args:
            self.infer(arg)

    def infer(self, node):
        if isinstance(node, StringLiteral):
            return "string"

        if isinstance(node, NumberLiteral):
            return "float" if isinstance(node.value, float) else "int"

        if isinstance(node, Identifier):
            if node.name not in self.symbols:
                raise DaniliumTypeError(
                    f"Undefined variable '{node.name}' at line {node.line}",
                    node.line,
                    self._line_text(node.line),
                )
            return self.symbols[node.name]

        if isinstance(node, BinOp):
            left_type = self.infer(node.left)
            right_type = self.infer(node.right)

            if node.op == "+":
                if left_type == "string" or right_type == "string":
                    if left_type != right_type:
                        raise DaniliumTypeError(
                            f"Type mismatch at line {node.line}\n\n"
                            f"cannot use '+' between {left_type} and {right_type}.",
                            node.line,
                            self._line_text(node.line),
                        )
                    return "string"
                return "float" if "float" in (left_type, right_type) else "int"

            if left_type not in ("int", "float") or right_type not in ("int", "float"):
                raise DaniliumTypeError(
                    f"Type mismatch at line {node.line}\n\n"
                    f"cannot use '{node.op}' between {left_type} and {right_type}.",
                    node.line,
                    self._line_text(node.line),
                )
            return "float" if "float" in (left_type, right_type) else "int"

        if isinstance(node, FunctionCall):
            self.check_call(node)
            return "void"

        raise DaniliumTypeError(f"Cannot infer type of node {node}", getattr(node, "line", 0))
