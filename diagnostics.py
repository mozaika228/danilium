"""Shared source diagnostic representation and CLI formatting."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    category: str
    message: str
    filename: str
    line: int
    column: int

    def format(self):
        message = next(
            (line.strip() for line in reversed(self.message.splitlines()) if line.strip()),
            self.message.strip(),
        )
        return f"error: {message}\n  --> {self.filename}:{self.line}:{self.column}"


def from_exception(error, filename="<input>"):
    """Convert a compiler/runtime exception to the common diagnostic shape."""
    from interpreter import DaniliumRuntimeError
    from lexer import LexError
    from parser import ParseError
    from type_checker import DaniliumTypeError

    if isinstance(error, LexError):
        category = "lexer"
    elif isinstance(error, ParseError):
        category = "parser"
    elif isinstance(error, DaniliumTypeError):
        category = "type checker"
    elif isinstance(error, DaniliumRuntimeError):
        category = "runtime"
    else:
        category = "runtime"

    return Diagnostic(
        category=category,
        message=getattr(error, "message", str(error)),
        filename=filename,
        line=max(1, getattr(error, "line", 1) or 1),
        column=max(1, getattr(error, "column", getattr(error, "col", 1)) or 1),
    )
