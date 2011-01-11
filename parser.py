import tokens
import ast

# semantic actions
def addlineno(node, lineno):
    if isinstance(node, ast.node):
        node.addlineno(lineno)
    return node

def pushTerminal(astType):
    def semanticAction(stack, token):
        stack.append(addlineno(astType(token.value), token.lineno))
    return semanticAction

def pushNonTerminal(astType, numArgs):
    def semanticAction(stack, token):
        args = []
        for i in range(numArgs):
            args.append(stack.pop())
        args = args[::-1]
        stack.append(addlineno(astType(*args), token.lineno))
    return semanticAction

def pushEmptyList(stack, token):
    stack.append([])

def appendToList(stack, token):
    if len(stack) == 1:
        print stack
    item = stack.pop()
 
    stack[-1].append(item)

def pushToken(stack, token):
    stack.append(token)
 
# grammar with semantic actions
start_symbol = 'program'
grammarWithActions = {
    'program': [[pushEmptyList, 'definitions', pushNonTerminal(ast.program, 1)]],
    'definitions': [['def', appendToList, 'definitions-tail']],
    'definitions-tail': [['definitions'],
                         []],
    'def': [['identifier', tokens.LPAREN, 'formals', tokens.RPAREN, tokens.COLON, 'type', 'body', pushNonTerminal(ast.functionDef, 4)]],
    'formals': [[pushEmptyList, 'nonemptyformals', pushNonTerminal(ast.formals, 1)],
                [pushEmptyList,                    pushNonTerminal(ast.formals, 1)]],
    'nonemptyformals': [['formal', appendToList, 'nonemptyformals-tail']],
    'nonemptyformals-tail': [[tokens.COMMA, 'nonemptyformals'],
                             []],
    'formal': [['identifier', tokens.COLON, 'type', pushNonTerminal(lambda x,y: (x,y), 2)]],
    'type': [[tokens.BOOLEAN, pushNonTerminal(lambda: ast.typename("boolean"), 0)],
             [tokens.INTEGER, pushNonTerminal(lambda: ast.typename("integer"), 0)]],
    'body': [['print', 'body', pushNonTerminal(ast.printBody, 2)],
             ['expr']],
    'print': [[tokens.PRINT, tokens.LPAREN, 'actuals', tokens.RPAREN]],
    'expr': [['boolexpr', 'exprtail']],
    'exprtail': [[tokens.OR,  pushToken, 'boolexpr', pushNonTerminal(ast.binaryExpr, 3), 'exprtail'],
                 [tokens.AND, pushToken, 'boolexpr', pushNonTerminal(ast.binaryExpr, 3), 'exprtail'],
                 []],
    'boolexpr': [['term', 'bootail']],
    'bootail': [[tokens.LANGLE, pushToken, 'term', pushNonTerminal(ast.binaryExpr, 3), 'bootail'],
                [tokens.EQUALS, pushToken, 'term', pushNonTerminal(ast.binaryExpr, 3), 'bootail'],
                []],
    'term': [['factor', 'termtail']],
    'termtail': [[tokens.PLUS,  pushToken, 'factor', pushNonTerminal(ast.binaryExpr, 3), 'termtail'],
                 [tokens.MINUS, pushToken, 'factor', pushNonTerminal(ast.binaryExpr, 3), 'termtail'],
                 []],
    'factor': [['atom', 'factortail']],
    'factortail': [[tokens.STAR,   pushToken, 'atom', pushNonTerminal(ast.binaryExpr, 3), 'factortail'], 
                   [tokens.DIVIDE, pushToken, 'atom', pushNonTerminal(ast.binaryExpr, 3), 'factortail'],
                   []],
    'atom': [[tokens.IF, 'expr', tokens.THEN, 'expr', tokens.ELSE, 'expr', tokens.ENDIF, pushNonTerminal(ast.ifExpr, 3)],
             [tokens.NOT, 'atom', pushNonTerminal(ast.notExpr, 1)],
             ['identifier', 'params'],
             [tokens.BOOLEANLIT, pushTerminal(ast.booleanlit)],
             [tokens.INTEGERLIT, pushTerminal(ast.integerlit)],
             [tokens.LPAREN, 'expr', tokens.RPAREN]],
    'identifier': [[tokens.IDENTIFIER, pushTerminal(ast.identifier)]],
    'params': [[tokens.LPAREN, 'actuals', tokens.RPAREN, pushNonTerminal(ast.functionCall, 2)],
               []],
    'actuals': [[pushEmptyList, 'nonemptyactuals', pushNonTerminal(ast.actuals, 1)],
                [pushEmptyList,                    pushNonTerminal(ast.actuals, 1)]],
    'nonemptyactuals': [['expr', appendToList, 'nonemptyactuals-tail']],
    'nonemptyactuals-tail': [[tokens.COMMA, 'nonemptyactuals'],
                             []],
}

# Strip semantic actions to build original grammar
grammar = {}
for symbol in grammarWithActions:
    grammar[symbol] = []
    for rule in grammarWithActions[symbol]:
        new_rule = []
        for atom in rule:
            if isinstance(atom, str) or isinstance(atom, tokens.token):
                new_rule.append(atom)
        grammar[symbol].append(new_rule)

# first and follow sets
def first(alpha):
    """first(alpha) -> set of terminals that alpha can begin with"""
    if isinstance(alpha, tokens.token):
        return set([alpha])
    elif isinstance(alpha, list):
        if alpha == []:
            return set([None]) # empty string
        else:
            result = first(alpha[0])
            if None in result:
                result.update(first(alpha[1:]))
            return result
    elif isinstance(alpha, str):
        union = set([])
        for production in grammar[alpha]:
            union.update(first(production))
        return union
    else:
        raise TypeError, "unknown type for first(alpha): %s" % type(alpha)


def follow(nonterm, visited=()):
    """follow(nonterm) -> set of terminals that can follow any derivation of nonterm"""
    if nonterm not in grammar:
        raise ValueError, "nonterminal %s is not defined in grammar" % nonterm
    result = set([])
    if nonterm == start_symbol: result.add(tokens.EOF)
    for symbol in grammar:
        for production in grammar[symbol]:
            while nonterm in production:
                index = production.index(nonterm)
                checked = False
                if index+1 < len(production):
                    new_set = first(production[index+1])
                    if None in new_set:
                        checked = True
                        new_set.remove(None)
                    result.update(new_set)
                else:
                    checked = True
                
                if checked and symbol not in visited:
                    result.update(follow(symbol, visited + (symbol,)))
                
                production = production[index+1:]

    return result

# build parse table
table = {}

for symbol in grammar:
    for index in range(len(grammar[symbol])):
        production = grammarWithActions[symbol][index]
        for terminal in first(grammar[symbol][index]):
            if terminal:
                if (symbol, terminal.name) in table:
                    print "two table entries for", symbol
                    print "    entry key: (%s, %s)" % (symbol, terminal.name)
                    print "    old table entry:", table[(symbol, terminal.name)]
                    print "    new table entry:", production
                    raise ValueError, "two table entries for %s" % symbol
                table[(symbol, terminal.name)] = production
            else:
                for terminal in follow(symbol):
                    if (symbol, terminal.name) in table:
                        print "two table entries for", symbol
                        print "    entry key: (%s, %s)" % (symbol, terminal.name)
                        print "    old table entry:", table[(symbol, terminal.name)]
                        print "    new table entry:", production
                        print "    ignoring it"
                        raise ValueError, "two table entries for %s" % symbol
                    else:
                        table[(symbol, terminal.name)] = production

def parse(toks):
    import scanner
    if not isinstance(toks, scanner.scan):
        toks = scanner.scan(toks)
    stack = [tokens.EOF, start_symbol]
    last_token = None
    semantic_stack = []
    while stack:
        if isinstance(stack[-1], tokens.token):
            if not stack[-1] == toks.peek():
                raise SyntaxError, "expected %s, got %s (line %s)" % (stack[-1], toks.peek(), toks.peek().lineno)
            stack.pop()
            last_token = toks.next()
        elif isinstance(stack[-1], str):                    
            if (stack[-1], toks.peek().name) not in table:
                raise SyntaxError, "expected %s, got %s (line %s)" % (stack[-1], toks.peek(), toks.peek().lineno)
            symbol = stack.pop()
            production = table[(symbol, toks.peek().name)]
            stack.extend(production[::-1])
        else:
            action = stack.pop()
            action(semantic_stack, last_token)
    assert len(semantic_stack) == 1
    return semantic_stack[-1]
    
    
