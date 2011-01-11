
class token(object):

    def __init__(self, name, value=None, lineno=None):
        self.name = name
        self.value = value
        self.lineno = lineno

    def __eq__(self, other):
        return isinstance(other, token) and self.name == other.name

    def __call__(self, value, lineno=None):
        return token(self.name, value if self.value else None, lineno)

    def __repr__(self):
        if self.value and self.value is not True:
            return "%s(%r)" % (self.name, self.value)
        else:
            return self.name
    

# Token types with semantic value
INTEGERLIT = token("INTEGERLIT", True)
BOOLEANLIT = token("BOOLEANLIT", True)
IDENTIFIER = token("IDENTIFIER", True)

# Token types without semantic value
INTEGER = token("INTEGER")
BOOLEAN = token("BOOLEAN")
IF = token("IF")
THEN = token("THEN")
ELSE = token("ELSE")
ENDIF = token("ENDIF")
MAIN = token("MAIN")
PRINT = token("PRINT")
AND = token("AND")
NOT = token("NOT")
OR = token("OR")
PLUS = token("PLUS")
MINUS = token("MINUS")
STAR = token("STAR")
DIVIDE = token("DIVIDE")
LANGLE = token("LANGLE")
EQUALS = token("EQUALS")
LPAREN = token("LPAREN")
RPAREN = token("RPAREN")
COLON = token("COLON")
COMMA = token("COMMA")
EOF = token("EOF")
