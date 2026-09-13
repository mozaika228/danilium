"""
Danilium Parser.

Grammar (0.2):

    program     := statement*
    statement   := let_stmt | if_stmt | while_stmt | fn_decl | return_stmt
                 | compound_assign | assignment | expression
    let_stmt    := "let" IDENTIFIER (":" TYPE)? "=" expression
    assignment  := IDENTIFIER (":" TYPE)? "=" expression
    compound    := IDENTIFIER ("+=" | "-=" | "*=" | "/=") expression
    if_stmt     := "if" expression "->" statement
                 | "if" expression "do" block
                       ("elif" expression "do" block)*
                       ("else" block)?
                   "end"
    while_stmt  := "while" expression "->" statement
                 | "while" expression "do" block "end"
    fn_decl     := "fn" IDENTIFIER "(" params? ")" "do" block "end"
    return_stmt := "return" expression?
    block       := statement* (until elif/else/end)

    expression  := or_expr
    or_expr     := and_expr ("or" and_expr)*
    and_expr    := equality ("and" equality)*
    equality    := comparison (("==" | "!=") comparison)*
    comparison  := addition (("<" | ">" | "<=" | ">=") addition)*
    addition    := term (("+" | "-") term)*
    term        := unary (("*" | "/") unary)*
    unary       := ("not" | "-") unary | primary
    primary     := STRING | NUMBER | TRUE | FALSE | IDENTIFIER | call
                 | "(" expression ")"
    call        := IDENTIFIER "(" (expression ("," expression)*)? ")"
"""

from lexer import TokenType
from ast_nodes import (
    Program,
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

COMPOUND_OPS = {
    TokenType.PLUSEQ: "+",
    TokenType.MINUSEQ: "-",
    TokenType.STAREQ: "*",
    TokenType.SLASHEQ: "/",
}

COMPARISON_OPS = {
    TokenType.LT: "<",
    TokenType.GT: ">",
    TokenType.LTE: "<=",
    TokenType.GTE: ">=",
}


class ParseError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line


class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

    # -- token helpers --------------------------------------------------

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

    # -- program / blocks -------------------------------------------------

    def parse(self):
        statements = []
        self.skip_newlines()
        while not self.check(TokenType.EOF):
            statements.append(self.parse_statement())
            self.skip_newlines()
        return Program(statements)

    def parse_block(self):
        """Parse statements until elif/else/end/EOF (used inside do...end)."""
        statements = []
        self.skip_newlines()
        stop = (TokenType.ELIF, TokenType.ELSE, TokenType.END, TokenType.EOF)
        while self.current().type not in stop:
            statements.append(self.parse_statement())
            self.skip_newlines()
        return statements

    # -- statements ---------------------------------------------------------

    def parse_statement(self):
        if self.check(TokenType.LET):
            self.advance()
            return self.parse_assignment()
        if self.check(TokenType.IF):
            return self.parse_if()
        if self.check(TokenType.WHILE):
            return self.parse_while()
        if self.check(TokenType.FN):
            return self.parse_fn()
        if self.check(TokenType.RETURN):
            return self.parse_return()
        if self.check(TokenType.IDENTIFIER):
            nxt = self.peek(1).type
            if nxt in (TokenType.EQUALS, TokenType.COLON):
                return self.parse_assignment()
            if nxt in COMPOUND_OPS:
                return self.parse_compound_assignment()
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

    def parse_compound_assignment(self):
        name_tok = self.expect(TokenType.IDENTIFIER)
        op_tok = self.advance()
        op = COMPOUND_OPS[op_tok.type]
        rhs = self.parse_expression()
        value = BinOp(op, Identifier(name_tok.value, name_tok.line), rhs, name_tok.line)
        return Assignment(name_tok.value, None, value, name_tok.line)

    def parse_if(self):
        line = self.expect(TokenType.IF).line
        condition = self.parse_expression()

        if self.check(TokenType.ARROW):
            self.advance()
            then_stmt = self.parse_statement()
            return If(condition, [then_stmt], [], None, line)

        self.expect(TokenType.DO, "Expected 'do' or '->' after the if-condition")
        then_block = self.parse_block()

        elif_clauses = []
        while self.check(TokenType.ELIF):
            self.advance()
            elif_cond = self.parse_expression()
            self.expect(TokenType.DO, "Expected 'do' after the elif-condition")
            elif_body = self.parse_block()
            elif_clauses.append((elif_cond, elif_body))

        else_block = None
        if self.check(TokenType.ELSE):
            self.advance()
            else_block = self.parse_block()

        self.expect(TokenType.END, "Expected 'end' to close the if-block")
        return If(condition, then_block, elif_clauses, else_block, line)

    def parse_while(self):
        line = self.expect(TokenType.WHILE).line
        condition = self.parse_expression()

        if self.check(TokenType.ARROW):
            self.advance()
            body_stmt = self.parse_statement()
            return While(condition, [body_stmt], line)

        self.expect(TokenType.DO, "Expected 'do' or '->' after the while-condition")
        body = self.parse_block()
        self.expect(TokenType.END, "Expected 'end' to close the while-block")
        return While(condition, body, line)

    def parse_fn(self):
        line = self.expect(TokenType.FN).line
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.LPAREN)
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.parse_param())
            while self.check(TokenType.COMMA):
                self.advance()
                params.append(self.parse_param())
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.DO, "Expected 'do' to start the function body")
        body = self.parse_block()
        self.expect(TokenType.END, "Expected 'end' to close the function body")
        return FnDecl(name_tok.value, params, body, line)

    def parse_param(self):
        name_tok = self.expect(TokenType.IDENTIFIER)
        type_annotation = None
        if self.check(TokenType.COLON):
            self.advance()
            type_tok = self.expect(TokenType.IDENTIFIER, "Expected a type name after ':'")
            type_annotation = type_tok.value
        return (name_tok.value, type_annotation)

    def parse_return(self):
        line = self.expect(TokenType.RETURN).line
        stop = (TokenType.NEWLINE, TokenType.END, TokenType.ELIF, TokenType.ELSE, TokenType.EOF)
        value = None
        if self.current().type not in stop:
            value = self.parse_expression()
        return Return(value, line)

    # -- expressions (precedence climbing) -----------------------------------

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check(TokenType.OR):
            op_tok = self.advance()
            right = self.parse_and()
            left = BinOp("or", left, right, op_tok.line)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check(TokenType.AND):
            op_tok = self.advance()
            right = self.parse_equality()
            left = BinOp("and", left, right, op_tok.line)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.check(TokenType.EQEQ) or self.check(TokenType.NOTEQ):
            op_tok = self.advance()
            op = "==" if op_tok.type == TokenType.EQEQ else "!="
            right = self.parse_comparison()
            left = BinOp(op, left, right, op_tok.line)
        return left

    def parse_comparison(self):
        left = self.parse_addition()
        while self.current().type in COMPARISON_OPS:
            op_tok = self.advance()
            right = self.parse_addition()
            left = BinOp(COMPARISON_OPS[op_tok.type], left, right, op_tok.line)
        return left

    def parse_addition(self):
        left = self.parse_term()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_term()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_term(self):
        left = self.parse_unary()
        while self.check(TokenType.STAR) or self.check(TokenType.SLASH):
            op_tok = self.advance()
            right = self.parse_unary()
            left = BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_unary(self):
        if self.check(TokenType.NOT):
            op_tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp("not", operand, op_tok.line)
        if self.check(TokenType.MINUS):
            op_tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp("-", operand, op_tok.line)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()

        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(tok.value, tok.line)

        if tok.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(tok.value, tok.line)

        if tok.type == TokenType.TRUE:
            self.advance()
            return BooleanLiteral(True, tok.line)

        if tok.type == TokenType.FALSE:
            self.advance()
            return BooleanLiteral(False, tok.line)

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
