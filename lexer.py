"""
Danilium Lexer.

Turns source code into a stream of tokens: IDENTIFIER, STRING, keywords
(IF, DO, END, ...), operators, etc.
"""


class TokenType:
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"

    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COLON = "COLON"
    COMMA = "COMMA"

    EQUALS = "EQUALS"          # =
    PLUS = "PLUS"              # +
    MINUS = "MINUS"            # -
    STAR = "STAR"              # *
    SLASH = "SLASH"            # /

    PLUSEQ = "PLUSEQ"          # +=
    MINUSEQ = "MINUSEQ"        # -=
    STAREQ = "STAREQ"          # *=
    SLASHEQ = "SLASHEQ"        # /=

    EQEQ = "EQEQ"              # ==
    NOTEQ = "NOTEQ"            # !=
    LT = "LT"                  # <
    GT = "GT"                  # >
    LTE = "LTE"                # <=
    GTE = "GTE"                # >=

    ARROW = "ARROW"            # ->

    # keywords
    IF = "IF"
    ELIF = "ELIF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    FN = "FN"
    RETURN = "RETURN"
    DO = "DO"
    END = "END"
    LET = "LET"
    TRUE = "TRUE"
    FALSE = "FALSE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    NEWLINE = "NEWLINE"
    EOF = "EOF"


class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexError(Exception):
    def __init__(self, message, line, col=0):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col


KEYWORDS = {
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "do": TokenType.DO,
    "end": TokenType.END,
    "let": TokenType.LET,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}

SINGLE_CHAR_TOKENS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
}

# Two-character operators, checked before falling back to single characters.
TWO_CHAR_TOKENS = {
    "->": TokenType.ARROW,
    "==": TokenType.EQEQ,
    "!=": TokenType.NOTEQ,
    "<=": TokenType.LTE,
    ">=": TokenType.GTE,
    "+=": TokenType.PLUSEQ,
    "-=": TokenType.MINUSEQ,
    "*=": TokenType.STAREQ,
    "/=": TokenType.SLASHEQ,
}

# Single-character operators that aren't the start of a two-char token above.
OPERATOR_TOKENS = {
    "=": TokenType.EQUALS,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "<": TokenType.LT,
    ">": TokenType.GT,
}

ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def error(self, message):
        raise LexError(message, self.line, self.col)

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ""

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def tokenize(self):
        tokens = []
        while self.pos < len(self.source):
            ch = self.peek()

            if ch in " \t\r":
                self.advance()
                continue

            if ch == "#":
                while self.pos < len(self.source) and self.peek() != "\n":
                    self.advance()
                continue

            if ch == "\n":
                line, col = self.line, self.col
                self.advance()
                tokens.append(Token(TokenType.NEWLINE, "\n", line, col))
                continue

            if ch == '"':
                tokens.append(self._read_string())
                continue

            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier_or_keyword())
                continue

            two = ch + self.peek(1)
            if two in TWO_CHAR_TOKENS:
                line, col = self.line, self.col
                self.advance()
                self.advance()
                tokens.append(Token(TWO_CHAR_TOKENS[two], two, line, col))
                continue

            if ch in SINGLE_CHAR_TOKENS:
                line, col = self.line, self.col
                self.advance()
                tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, line, col))
                continue

            if ch in OPERATOR_TOKENS:
                line, col = self.line, self.col
                self.advance()
                tokens.append(Token(OPERATOR_TOKENS[ch], ch, line, col))
                continue

            self.error(f"Unexpected character {ch!r}")

        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens

    def _read_string(self):
        line, col = self.line, self.col
        self.advance()  # opening quote
        chars = []
        while True:
            if self.pos >= len(self.source):
                self.error("Unterminated string literal")
            ch = self.peek()
            if ch == '"':
                self.advance()
                break
            if ch == "\\":
                self.advance()
                esc = self.advance()
                chars.append(ESCAPES.get(esc, esc))
                continue
            chars.append(self.advance())
        return Token(TokenType.STRING, "".join(chars), line, col)

    def _read_number(self):
        line, col = self.line, self.col
        chars = []
        is_float = False
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == "."):
            if self.peek() == ".":
                if is_float:
                    break
                is_float = True
            chars.append(self.advance())
        text = "".join(chars)
        value = float(text) if is_float else int(text)
        return Token(TokenType.NUMBER, value, line, col)

    def _read_identifier_or_keyword(self):
        line, col = self.line, self.col
        chars = []
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == "_"):
            chars.append(self.advance())
        text = "".join(chars)
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        return Token(token_type, text, line, col)
