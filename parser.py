"""
Danilium Parser.

Turns a token stream into an AST (Program of statements).

Supported grammar in 0.1:

    program     := statement*
    statement   := assignment | expression
    assignment  := IDENTIFIER (":" IDENTIFIER)? "=" expression
    expression  := term (("+" | "-") term)*
    term        := STRING | NUMBER | IDENTIFIER | call | "(" expression ")"
    call        := IDENTIFIER "(" (expression ("," expression)*)? ")"
"""

from lexer import TokenType
from ast_nodes import (
    Program,
    Assignment,
    FunctionCall,
    BinOp,
    StringLiteral,
    NumberLiteral,
    Identifier,
)


class ParseError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line


class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def check(self, type_):
        return self.current().type == type_

    def expect(self, type_, message=None):
        if not self.check(type_):
            tok = self.current()
            raise ParseError(
                message or f"Expected {type_} but found {tok.type} ({tok.value!r})",
                tok.line,
            )
        return self.advance()

    def skip_newlines(self):
        while self.check(TokenType.NEWLINE):
            self.advance()

    def parse(self):
        statements = []
        self.skip_newlines()
        while not self.check(TokenType.EOF):
            statements.append(self.parse_statement())
            self.skip_newlines()
        return Program(statements)

    def parse_statement(self):
        if self.check(TokenType.IDENTIFIER):
            nxt = self.peek(1).type
            if nxt in (TokenType.EQUALS, TokenType.COLON):
                return self.parse_assignment()
        return self.parse_expression()

    def parse_assignment(self):
        name_tok = self.expect(TokenType.IDENTIFIER)
        type_annotation = None
        if self.check(TokenType.COLON):
            self.advance()
            type_tok = self.expect(TokenType.IDENTIFIER, "Expected a type name after ':'")
            type_annotation = type_tok.value
        self.expect(TokenType.EQUALS)
        value = self.parse_expression()
        return Assignment(name_tok.value, type_annotation, value, name_tok.line)

    def parse_expression(self):
        left = self.parse_term()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_term()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_term(self):
        tok = self.current()

        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(tok.value, tok.line)

        if tok.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(tok.value, tok.line)

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.IDENTIFIER:
            name_tok = self.advance()
            if self.check(TokenType.LPAREN):
                self.advance()
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.check(TokenType.COMMA):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN)
                return FunctionCall(name_tok.value, args, name_tok.line)
            return Identifier(name_tok.value, name_tok.line)

        raise ParseError(f"Unexpected token {tok.type} ({tok.value!r})", tok.line)
