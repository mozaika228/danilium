"""AST node definitions for Danilium."""


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


class UnaryOp(Node):
    def __init__(self, op, operand, line):
        self.op = op
        self.operand = operand
        self.line = line


class StringLiteral(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class NumberLiteral(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class BooleanLiteral(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class Identifier(Node):
    def __init__(self, name, line):
        self.name = name
        self.line = line


class If(Node):
    """
    if cond -> stmt                          (then_block == [stmt], no elif/else)
    if cond do ... elif cond do ... else ... end
    """

    def __init__(self, condition, then_block, elif_clauses, else_block, line):
        self.condition = condition
        self.then_block = then_block            # list[Node]
        self.elif_clauses = elif_clauses          # list[(condition, block)]
        self.else_block = else_block              # list[Node] | None
        self.line = line


class While(Node):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body                          # list[Node]
        self.line = line


class FnDecl(Node):
    def __init__(self, name, params, body, line):
        self.name = name
        self.params = params                      # list[(name, type_annotation | None)]
        self.body = body                           # list[Node]
        self.line = line


class Return(Node):
    def __init__(self, value, line):
        self.value = value                        # Node | None
        self.line = line
