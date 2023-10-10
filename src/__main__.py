import sys
from collections import defaultdict


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
    ASM = "ASM" 
    COMMA = "COMMA"
    NORET = "NORET"


class Token:
    def __init__(self, kind: str, value=None, lnum=None, length=None, offset=None) -> None:
        self.kind = kind
        self.value = value
        self.lnum = lnum
        self.length = length
        self.offset = offset

    def __str__(self) -> str:
        return f"Token({self.kind}, {self.value})"


class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.lines = self.code.split("\n")
        self.index = 0
        self.buffer = ""
        self.line_num = 0
        self.line_offset = 0
        self.line_change = 0

    def token(self, kind, value=None):
        return Token(kind, value, self.line_num, self.line_change, self.line_offset)

    def error(self, message: str):
        line = self.lines[self.line_num].lstrip(" ")
        print(f"SYNTAX ERROR: {message}")
        print(f"{self.line_num} |    {line}")
        print(' ' * (len(str(self.line_num)) + 4 + self.line_offset + 1) + "^" * self.line_change)
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
            "+": TokenKind.PLUS,
            "*": TokenKind.TIMES,
            "-": TokenKind.MINUS,
            "/": TokenKind.DIVIDE,
            "%": TokenKind.MODULO,
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            "{": TokenKind.LSCOPE,
            "}": TokenKind.RSCOPE,
            ";": TokenKind.SEMICOLON,
            ",": TokenKind.COMMA,
        }
        if  self.current() in basic.keys():
            t = basic[self.current()]
            self.advance()
            return self.token(t)

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
                            return self.token(kind, value)
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
                            return self.token(kind, value)
                        except:
                            self.invalid_literal_for(self.buffer, "bin")

            case '"':
                self.advance()
                while self.current() != '"' and self.current() != '' and self.current() != "\n":
                    self.buffer += self.current()
                    self.advance()
                match (self.current()):
                    case '"':
                        self.advance()
                        return self.token(TokenKind.STRING, self.buffer)
                    case '' | "\n":
                        self.error("Expected end of string")

            case "\n":
                self.line_num += 1
                self.line_offset = 0
                self.advance()
                self.line_change = 0
                return self.token(TokenKind.EOL)

            case "#":
                while self.current() != "\n" and self.current() != "":
                    self.advance()
                return self.token(TokenKind.EOL)

    def _next(self) -> Token:
        if self.index >= len(self.code):
            return self.token(TokenKind.EOF, None)

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
                return self.token(TokenKind.BYTE if value <= 255 else TokenKind.INT16,
                                value)
            match (self.buffer):
                case "fn":
                    return self.token(TokenKind.FUNCTION)
                case "while":
                    return self.token(TokenKind.WHILE)
                case "if":
                    return self.token(TokenKind.IF)
                case "ret":
                    return self.token(TokenKind.RETURN)
                case "buf":
                    return self.token(TokenKind.BUFFER)
                case "const":
                    return self.token(TokenKind.CONST)
                case "void" | "byte" | "int" | "ptr":
                    return self.token(TokenKind.TYPE, self.buffer)
                case "asm":
                    return self.token(TokenKind.ASM)
                case "noret":
                    return self.token(TokenKind.NORET)
                case _:
                    return self.token(TokenKind.IDENTIFIER, self.buffer)

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
.label __TUNGSTEN_FUNCTION_JBA
.alloc 2
.label __TUNGSTEN_FUNCION_RETVAL
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
        self.emit_data_label(name)
        self.emit_alloc(size)

    def emit_data_label(self, label):
        self.data_section += f"\n.label {label}"

    def emit_text_label(self, label):
        self.text_section += f"\n.label {label}"
        
    def emit_alloc(self, size):
        self.data_section += f"\n.alloc {size}"

    def emit_asm_text(self, code):
        self.text_section += f"\n{code}"


class Scope:
    def __init__(self, name, parent) -> None:
        self.name = name
        self.symbols = {}
        self.parent = parent
        self.unnamed_scope_cout = 0
        self.functions = []

    def header(self):
        return f"__TUNGSTEN_START_{self.name}"

    def footer(self):
        return f"__TUNGSTEN_END_{self.name}"

    def map_generic(self, key, value):
        self.symbols.__setitem__(key, value)

    def map_variable(self, name):
        self.symbols.__setitem__(name, f"BUFFER_{self.name}_{name}")

    def map_const(self, name):
        self.symbols.__setitem__(name, f"CONST_{self.name}_{name}")

    def map_function(self, name):
        self.symbols.__setitem__(name, f"FUNCTION_{self.name}_{name}")

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

    def add_function(self, signature):
        self.functions.append(signature)


class FunctionSignature:
    def __init__(self, name, args, ret_type) -> None:
        self.name = name
        self.args = args
        self.ret_type = ret_type
        self.returned = False


class Variable:
    def __init__(self, name, size, token) -> None:
        self.name = name
        self.size = size
        self.token = token


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        self.emitter = Emitter()
        self.signature = None
        self.scope = Scope("_GLOBAL", None)
        self._cur = None

    def error(self, message: str, token=None):
        target = token if token != None else self._cur
        line = self.lexer.lines[target.lnum].lstrip(" ")
        print(f"PARSER ERROR: {message}")
        print(f"{target.lnum} |    {line}")
        print(' ' * (len(str(target.lnum)) + 4 + target.offset + 3) + "^" * target.length)
        exit(-3)

    def next(self):
        token = self.lexer.next()
        while token.kind == TokenKind.EOL:
            token = self.lexer.next()
        self._cur = token
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
                    self.parse_function()
                    require_semicolon = False
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
                case TokenKind.ASM:
                    self.parse_asm()
                case TokenKind.NORET:
                    self.parse_noret()
                case TokenKind.EOF:
                    break

            if require_semicolon:
                self.expect(TokenKind.SEMICOLON)
        
        if self.scope.name != "_GLOBAL":
            self.error("Code does not end in _GLOBAL scope")

    def parse_buffer(self):
        var = self._collect_buf()
        self._alloc_var(var)
        
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
        if name == "main":
            self.emitter.emit_text_label("_main")
        scope = Scope(name, self.scope)
        self.scope = scope
        if self.signature != None:
            self.scope.map_generic("__ret", "__TUNGSTEN_FUNCION_RETVAL")
            self.scope.map_generic("__start", self.scope.header())
            self.scope.map_generic("__end", self.scope.footer())
            for arg in self.signature.args:
                self._alloc_var(arg)
        self.emitter.emit_text_label(self.scope.header())

    def parse_end_scope(self):
        if self.signature != None and self.signature.name == self.scope.name:
            if self.signature.ret_type != "void" and not self.signature.returned and self.signature.name == self.scope.name:
                self.error(f"Function `{self.signature.name}` of type `{self.signature.ret_type}` does not return any value")
            self.signature = None
        self.emitter.emit_text_label(self.scope.footer())
        self.scope = self.scope.parent

    def parse_function(self):
        if self.scope.name != "_GLOBAL":
            self.error("Unexpected nested function")
        name = self.expect(TokenKind.IDENTIFIER)
        type = None
        next = self.expect(TokenKind.LPAREN, TokenKind.TYPE)
        match (next.kind):
            case TokenKind.LPAREN:
                # Function has arguments -- TO BE IMPLEMENTED
                self.signature = FunctionSignature(name.value, [], None)

                while True:
                    var = self._collect_buf()
                    self.signature.args.append(var)
                    sep = self.expect(TokenKind.RPAREN, TokenKind.COMMA)
                    if sep.kind == TokenKind.RPAREN:
                        break
                self.signature.ret_type = self.expect(TokenKind.TYPE).value

            case TokenKind.TYPE:
                type = next.value
                self.signature = FunctionSignature(name.value, [], type)
        self.scope.functions.append(self.signature)

    def parse_asm(self):
        code = self.expect(TokenKind.STRING)
        if self.signature == None:
            self.error("Unexpected Assembly code outside function")
        self.emitter.emit_asm_text(self._parse_asm(code.value))

    def parse_noret(self):
        if self.signature == None:
            self.error("Unexpected `noret` outside of function")
        self.signature.returned = True

    def _collect_buf(self):
        name = self.expect(TokenKind.IDENTIFIER)
        type = self.expect(TokenKind.TYPE, TokenKind.BYTE)
        type_size = 0
        match (type.kind):
            case TokenKind.TYPE:
                match (type.value):
                    case "byte":
                        type_size = 1
                    case "int" | "ptr":
                        type_size = 2
            case TokenKind.BYTE:
                type_size = type.value

        return Variable(name.value, type_size, name)

    def _alloc_var(self, var):
        if self.scope.has_sym_strict(var.name):
            self.error(f"Symbol `{var.name}` already declared in scope `{self.scope.name}`", var.token)
        if var.size == 0:
            self.error(f"Cannot allocate symbol `{var.name}` of type `void`")

        self.scope.map_variable(var.name)
        self.emitter.emit_buffer(self.scope.get_sym(var.name), var.size)
            
    def _parse_asm(self, code):
        i = 0
        out = ""
        while i < len(code):
            if code[i] == "%":
                i += 1
                var_name = ""
                while i < len(code) and (code[i].isalnum() or code[i] == "_"):
                    var_name += code[i]
                    i += 1
                if not self.scope.has_sym(var_name):
                    self.error(f"Undeclared symbol `{var_name}` used in Embedded Assembly code")
                sym = self.scope.get_sym(var_name)
                out += sym
                continue
            out += code[i]
            i += 1
        return out


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
