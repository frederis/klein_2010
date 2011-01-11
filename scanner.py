import tokens

# Setting up the DFA
transitions = {
    ('start','-'):'minus',
    ('start','0'):'zero',
    ('start','+'):'plus',
    ('start','*'):'star',
    ('start','/'):'divide',
    ('start','='):'equals',
    ('start','<'):'langle',
    ('start','('):'lparen',
    ('start',')'):'rparen',
    ('start',':'):'colon',
    ('start',','):'comma',
    ('integerlit','0'):'integerlit',
    ('identifier','0'):'identifier'
}

for char in 'abcdefghijklmnopqrstuvwxyz':
    transitions[('start',char)] = 'identifier'
    transitions[('start',char.upper())] = 'identifier'
    transitions[('identifier',char)] = 'identifier'
    transitions[('identifier',char.upper())] = 'identifier'

for num in '123456789':
    transitions[('identifier',num)] = 'identifier'
    transitions[('start',num)] = 'integerlit'
    transitions[('integerlit',num)] = 'integerlit'
    transitions[('minus',num)] = 'integerlit'

# How we handle the 'identifier' end state
def handleIdentifiers(name, lineno=None):
    return {
        'integer':tokens.INTEGER,
        'boolean':tokens.BOOLEAN,
        'if':tokens.IF,
        'not':tokens.NOT,
        'or':tokens.OR,
        'and':tokens.AND,
        'then':tokens.THEN,
        'else':tokens.ELSE,
        'endif':tokens.ENDIF,
        'print':tokens.PRINT,
        'true':tokens.BOOLEANLIT,
        'false':tokens.BOOLEANLIT,
    }.get(name, tokens.IDENTIFIER)(name, lineno)


def handleIntegers(name, lineno=None):
    linenoAddendum = " (line %s)." % lineno if lineno else "."
    if int(name) >= 2**32:
        raise SyntaxError, "integer literal too high" + linenoAddendum
    if int(name) < -2**32:
        raise SyntaxError, "integer literal too low" + linenoAddendum
    return tokens.INTEGERLIT(name, lineno)
    
# What tokens the endstates correspond to
endstates = {
    'plus':tokens.PLUS,
    'star':tokens.STAR,
    'divide':tokens.DIVIDE,
    'langle':tokens.LANGLE,
    'equals':tokens.EQUALS, 
    'lparen':tokens.LPAREN,
    'rparen':tokens.RPAREN,
    'colon':tokens.COLON,
    'comma':tokens.COMMA,
    'identifier':handleIdentifiers,
    'zero':tokens.INTEGERLIT,
    'integerlit':handleIntegers,
    'minus':tokens.MINUS,
}

# scan class -- you can get the next token, one at a time, or you can just.
class scan(object):
    '''scan(code) -> iterable with tokens

    scan(code) returns a scan object, which you can use in a few different ways:
        - To get a list of all the tokens in the code, use list(scan(code))
        - To loop over each token in the code, use  for token in scan(code)...
        - For more finely-controlled scanning, save the result of scan(code),
        and use the next() method to get the each token.

    Potential improvements:
        - add a peek() method, which would allow one to look at the next token
        without consuming it. This could also be implemented as a separate
        class, in order to separate concerns.

    >>> list(scan(''))
    [EOF]
    >>> try: list(scan('foo@gmail.com'))
    ... except SyntaxError, e: print e
    Invalid token: @
    >>> list(scan('main( x : integer ) : integer'))
    [MAIN, LPAREN, IDENTIFIER('x'), COLON, INTEGER, RPAREN, COLON, INTEGER, EOF]
    >>> list(scan('foo123bar print -34 - 34'))
    [IDENTIFIER('foo123bar'), PRINT, INTEGERLIT('-34'), MINUS, INTEGERLIT('34'), EOF]
    >>> list(scan('x < 0+y'))
    [IDENTIFIER('x'), LANGLE, INTEGERLIT('0'), PLUS, IDENTIFIER('y'), EOF]
    >>> list(scan('09'))
    [INTEGERLIT('0'), INTEGERLIT('9'), EOF]
    >>> list(scan('a \\n b \\n c \\n\\n\\n// lol \\n d'))
    [IDENTIFIER('a'), IDENTIFIER('b'), IDENTIFIER('c'), IDENTIFIER('d')]
    '''

    def __init__(self, code):
        self.code = code
        self.lookahead = None
        self.eof = False
        self.lineno = 1

    def __iter__(self):
        return self

    def next(self):
        if self.lookahead:
            result = self.lookahead
            self.lookahead = None
        else:
            result = self.scan_next()
        return result
    
    def peek(self):
        if not self.lookahead:
            self.lookahead = self.scan_next()
        return self.lookahead
    
    def scan_next(self):
        '''self.scan_next() -> token, or raise StopIteration

        Scan the next token. If there are no tokens left, raise the
        StopIteration exception.

        When using self.next(), the input string is consumed in the process
        of scanning the next token.
        '''
        self.strip()
        if self.code == '':
            if self.eof:
                raise StopIteration
            else:
                self.eof = True
                return tokens.EOF(None, self.lineno)
        state = 'start'
        index = 0
        while index<len(self.code) and (state,self.code[index]) in transitions:
            state = transitions[(state,self.code[index])]
            index += 1
        text = self.code[:index]
        self.code = self.code[index:]
        if state in endstates:
            return endstates[state](text, self.lineno)
        else:
            raise SyntaxError, "Invalid token (line %s): " % self.lineno + text + self.code[0]

    def strip(self):
        '''self.strip()

        Remove whitespace and comments from the beginning of the input string.
        '''
        self.code = self.code.lstrip(' \t\r')
        while self.code[:2] == '//' or self.code[:1] == '\n':
            index = self.code.find('\n')
            if index == -1:
                self.code = ''
            else:
                self.code = self.code[index+1:].lstrip(' \t\r')
                self.lineno += 1
                self.check_include()
                
    def check_include(self):
        import sys
        if not ('-i' in sys.argv or '--include' in sys.argv):
            return
        directive = '#include'
        if self.code[:len(directive)] == directive:
            self.code = self.code[len(directive):].lstrip(' \t')
            if not self.code or self.code[0] != '"':
                raise SyntaxError, "expected filename after #include (line %s)" % self.lineno
            self.code = self.code[1:]
            index = self.code.find('"')
            if index == -1:
                raise SyntaxError, "mismatched quote after #include (line %s)" % self.lineno
            filename = self.code[:index]
            self.code = ' '+self.code[index+1:]
            self.include(filename)
    
    def include(self, file):
        self.code = open(file).read().replace('\n', ' ') + self.code
        self.code = self.code.lstrip(' \t\r')


if __name__ == '__main__':
    import doctest
    doctest.testmod()

