"""
Danilium Lexer.

Turns source code like:

    run("Hello, World!")

into a stream of tokens: IDENTIFIER, LPAREN, STRING, RPAREN, ...
"""


class TokenType:
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EQUALS = "EQUALS"
    COLON = "COLON"
    COMMA = "COMMA"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
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


SINGLE_CHAR_TOKENS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "=": TokenType.EQUALS,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
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
                tokens.append(self._read_identifier())
                continue

            if ch in SINGLE_CHAR_TOKENS:
                line, col = self.line, self.col
                self.advance()
                tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, line, col))
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

    def _read_identifier(self):
        line, col = self.line, self.col
        chars = []
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == "_"):
            chars.append(self.advance())
        return Token(TokenType.IDENTIFIER, "".join(chars), line, col)
