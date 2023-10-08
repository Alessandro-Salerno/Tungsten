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
    TYPE = "TYPE"
    CONST = "CONST"


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
                case "const":
                    return Token(TokenKind.CONST)
                case "void" | "byte" | "int" | "ptr":
                    return Token(TokenKind.TYPE, self.buffer)
                case _:
                    return Token(TokenKind.IDENTIFIER, self.buffer)

    def next(self):
        self.clear_buffer()
        _next = self._next()
        self.line_offset += self.line_change
        return _next


class Emitter:
    def __init__(self):
        self.data_section = """
# Tungsten Compiler
# Generated data
.section data
.label _swap
.alloc 2
"""
        self.text_section = """
# Tungsten Compiler
# Generated code
.section text
"""
        self.constants = """
# Tungsten Compiler
# Constants
.set void 0
.set byte 1
.set int 2
.set ptr 2
"""

    def build(self):
        return self.constants + "\n" + self.text_section + "\n" + self.data_section

    def emit_const(self, name, value):
        self.constants += f".set {name} {value}"

    def emit_buffer(self, name, size):
        self.data_section += f"\n.label {name}"
        self.data_section += f"\n.alloc {size}"


class Scope:
    def __init__(self, name, parent) -> None:
        self.name = name
        self.symbols = {}
        self.parent = parent
        self.unnamed_scope_cout = 0

    def map_variable(self, name):
        self.symbols.__setitem__(name, f"BUFFER_{self.name}_{name}")

    def map_const(self, name):
        self.symbols.__setitem__(name, f"CONST_{self.name}_{name}")

    def has_sym_strict(self, name):
        return name in self.symbols

    def has_sym(self, name):
        if self.has_sym_strict(name):
            return True
        return self.parent != None and self.parent.has_sym(name)

    def get_sym(self, name):
        if self.has_sym_strict(name):
            return self.symbols[name]
        if self.parent != None:
            return self.parent.get_sym(name)
        return None

    def new_subscope(self):
        name = f"{self.name}{self.unnamed_scope_cout}"
        self.unnamed_scope_cout += 1
        return name


class FunctionSignature:
    def __init__(self, name, args, ret_type) -> None:
        self.name = name
        self.args = args
        self.ret_type = ret_type


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        self.emitter = Emitter()
        self.signature = None
        self.scope = Scope("_GLOBAL", None)

    def error(self, message: str):
        print(f"PARSER ERROR: {message}")
        exit(-3)

    def next(self):
        token = self.lexer.next()
        while token.kind == TokenKind.EOL:
            token = self.lexer.next()
        return token

    def expect(self, *token_kinds):
        token = self.next()

        if token.kind not in token_kinds:
            self.error(f"Unexpected token `{token}`")
        
        return token

    def parse(self):
        while True:
            require_semicolon = True
            match (self.next().kind):
                case TokenKind.BUFFER:
                    self.parse_buffer()
                case TokenKind.CONST:
                    self.parse_const()
                case TokenKind.FUNCTION:
                    pass
                case TokenKind.IF:
                    pass
                case TokenKind.WHILE:
                    pass
                case TokenKind.IDENTIFIER:
                    pass
                case TokenKind.RETURN:
                    pass
                case TokenKind.LSCOPE:
                    self.parse_new_scope()
                    require_semicolon = False
                case TokenKind.RSCOPE:
                    self.parse_end_scope()
                    require_semicolon = False
                case TokenKind.EOF:
                    break

            if require_semicolon:
                self.expect(TokenKind.SEMICOLON)

    def parse_buffer(self):
        name = self.expect(TokenKind.IDENTIFIER)
        type = self.expect(TokenKind.TYPE)
        if self.scope.has_sym_strict(name.value):
            self.error(f"Symbol `{name.value}` already declared in scope `{self.scope.name}`")
        self.scope.map_variable(name.value)
        type_size = 0
        match (type.value):
            case "byte":
                type_size = 1
            case "int" | "ptr":
                type_size = 2

        self.emitter.emit_buffer(self.scope.get_sym(name.value), type_size)

    def parse_const(self):
        name = self.expect(TokenKind.IDENTIFIER)
        self.expect(TokenKind.EQUALS)
        value = self.expect(TokenKind.IDENTIFIER, TokenKind.BYTE, TokenKind.INT16, TokenKind.STRING, TokenKind.TYPE)
        if self.scope.has_sym_strict(name.value):
            self.error(f"Symbol `{name.value}` already declared in scope `{self.scope.name}`")
        self.scope.map_const(name.value)
        self.emitter.emit_const(self.scope.get_sym(name.value), value.value)

    def parse_new_scope(self):
        name = self.signature.name if self.signature != None else self.scope.new_subscope()
        scope = Scope(name, self.scope)
        self.scope = scope

    def parse_end_scope(self):
        if self.signature != None and self.signature.name == self.scope.name:
            self.signature = None
        self.scope = self.scope.parent


def main(argv: list):
    if len(argv) != 1:
        print("ERROR: Expected 1 argument")
        return -1

    code = ""
    with open(argv[0], "r") as file:
        code = file.read()

    lexer = Lexer(code)
    parser = Parser(lexer)
    parser.parse()
    with open("out.asm", "w") as file:
        file.write(parser.emitter.build())


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
