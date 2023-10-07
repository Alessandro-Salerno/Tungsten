import sys


class TokenKind:
    EOL = "EOL"
    EOF = "EOF"
    BYTE = "BYTE"
    INT16 = "INT16"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    PLUS = "PLUS"
    MINUS = "MINUS"
    TIMES = "TIMES"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"
    LSCOPE = "LSCOPE"
    RSCOPE = "RSCOPE"
    FUNCTION = "FUNCTION"
    WHILE = "WHILE"
    IF = "IF"
    EQUALS = "EQUALS"
    RETURN = "RETURN"
    SEMICOLON = "SEMICOLON"
    BUFFER = "BUFFER"


class Token:
    def __init__(self, kind: str, value=None) -> None:
        self.kind = kind
        self.value = value

    def __str__(self) -> str:
        return f"Token({self.kind}, {self.value})"


class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.index = 0
        self.buffer = ""
        self.line_num = 0
        self.line_offset = 0
        self.line_change = 0

    def error(self, message: str):
        lines = self.code.split("\n")
        line = lines[self.line_num]
        n_spaces =  line.count(" ") - 1
        print(f"SYNTAX ERROR: {message}")
        print(f"{self.line_num}|    {line}")
        print(' ' * (len(str(self.line_num)) + 4 + n_spaces + self.line_offset) + "^" * self.line_change)
        exit(-2)

    def unknown_token_error(self, token):
        self.error(f"Unknown token `{token}`")

    def invalid_literal_for(self, literal, type):
        self.error(f"Invaid literal `{literal}` for type `{type}`")

    def current(self) -> str:
        if self.index >= len(self.code):
            return ""

        return self.code[self.index]

    def advance(self, qty=1):
        self.index += qty
        self.line_change += qty

    def clear_buffer(self):
        self.buffer = ""
        self.line_change = 0

    def token_grabbed(self):
        return self.buffer != ""

    def _next_by_sym(self) -> Token | None:
        basic = {
            "+": Token(TokenKind.PLUS),
            "*": Token(TokenKind.TIMES),
            "-": Token(TokenKind.MINUS),
            "/": Token(TokenKind.DIVIDE),
            "%": Token(TokenKind.MODULO),
            "(": Token(TokenKind.LPAREN),
            ")": Token(TokenKind.RPAREN),
            "{": Token(TokenKind.LSCOPE),
            "}": Token(TokenKind.RSCOPE),
            "=": Token(TokenKind.EQUALS),
            ";": Token(TokenKind.SEMICOLON),
        }
        if  self.current() in basic.keys():
            t = basic[self.current()]
            self.advance()
            return t

        match (self.current()):
            case "0":
                self.advance()
                match (self.current()):
                    case "x":
                        self.advance()
                        while self.current().isalnum():
                            self.buffer += self.current()
                            self.advance()
                        try:
                            value = int(self.buffer, 16)
                            kind = TokenKind.BYTE if value <= 255 else TokenKind.INT16
                            return Token(kind, value)
                        except:
                            self.invalid_literal_for(self.buffer, "hex")

                    case "b":
                        self.advance()
                        while self.current() == "0" or self.current() == "1":
                            self.buffer += self.current()
                            self.advance()
                        try:
                            value = int(self.buffer, 2)
                            kind = TokenKind.BYTE if value <= 255 else TokenKind.INT16
                            return Token(kind, value)
                        except:
                            self.invalid_literal_for(self.buffer, "bin")

            case '"':
                self.advance()
                while self.current() != '"' and self.current() != '':
                    self.buffer += self.current()
                    self.advance()
                match (self.current()):
                    case '"':
                        self.advance()
                        return Token(TokenKind.STRING, self.buffer)
                    case '':
                        self.error("Expected end of string")

            case "\n":
                self.line_num += 1
                self.line_offset = 0
                self.advance()
                return Token(TokenKind.EOL)

    def _next(self) -> Token:
        if self.index >= len(self.code):
            return Token(TokenKind.EOF, None)

        while self.current() == " " or self.current() == "\t":
            self.advance()
            self.clear_buffer()

        _by_sym = self._next_by_sym()
        if _by_sym != None:
            return _by_sym
        
        while self.current().isdecimal():
            self.buffer += self.current()
            self.advance()

        if not self.token_grabbed():
            while self.current().isalnum() or self.current() == "_":
                self.buffer += self.current()
                self.advance()

        if self.token_grabbed():
            if self.buffer.isdecimal():
                value = int(self.buffer)
                return Token(TokenKind.BYTE if value <= 255 else TokenKind.INT16,
                                value)
            match (self.buffer):
                case "fn":
                    return Token(TokenKind.FUNCTION)
                case "while":
                    return Token(TokenKind.WHILE)
                case "if":
                    return Token(TokenKind.IF)
                case "ret":
                    return Token(TokenKind.RETURN)
                case "buf":
                    return Token(TokenKind.BUFFER)
                case _:
                    return Token(TokenKind.IDENTIFIER, self.buffer)

    def next(self):
        self.clear_buffer()
        _next = self._next()
        self.line_offset += self.line_change
        return _next


def main(argv: list):
    if len(argv) != 1:
        print("ERROR: Expected 1 argument")
        exit(-1)

    code = ""
    with open(argv[0], "r") as file:
        code = file.read()

    lexer = Lexer(code)
    while True:
        next = lexer.next()
        print(next)
        if next.kind == TokenKind.EOF:
            break


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
