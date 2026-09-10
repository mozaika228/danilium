"""
Danilium Interpreter.

Walks the AST and actually executes the program (Danilium 0.1's runtime —
no bytecode/VM yet, just a straightforward tree-walker).
"""

from ast_nodes import Assignment, FunctionCall, BinOp, StringLiteral, NumberLiteral, Identifier


class DaniliumRuntimeError(Exception):
    pass


class Interpreter:
    def __init__(self):
        self.variables = {}

    def run(self, program):
        for stmt in program.statements:
            self.execute(stmt)

    def execute(self, stmt):
        if isinstance(stmt, Assignment):
            self.variables[stmt.name] = self.evaluate(stmt.value)
            return None
        return self.evaluate(stmt)

    def evaluate(self, node):
        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, NumberLiteral):
            return node.value

        if isinstance(node, Identifier):
            return self.variables[node.name]

        if isinstance(node, BinOp):
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
            raise DaniliumRuntimeError(f"Unknown operator {node.op}")

        if isinstance(node, FunctionCall):
            return self.call_builtin(node)

        raise DaniliumRuntimeError(f"Cannot evaluate node {node}")

    def call_builtin(self, node: FunctionCall):
        if node.name == "run":
            value = self.evaluate(node.args[0])
            print(value)
            return None
        raise DaniliumRuntimeError(f"Unknown function '{node.name}'")
