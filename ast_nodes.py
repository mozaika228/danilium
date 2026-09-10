"""AST node definitions for Danilium (0.1)."""


class Node:
    pass


class Program(Node):
    def __init__(self, statements):
        self.statements = statements


class Assignment(Node):
    def __init__(self, name, type_annotation, value, line):
        self.name = name
        self.type_annotation = type_annotation
        self.value = value
        self.line = line


class FunctionCall(Node):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line


class BinOp(Node):
    def __init__(self, op, left, right, line):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class StringLiteral(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class NumberLiteral(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class Identifier(Node):
    def __init__(self, name, line):
        self.name = name
        self.line = line
