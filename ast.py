
class node(object):
    def accept(self, visitor, *args):
        typename = type(self).__name__
        return getattr(visitor, 'visit_'+typename)(self, *args)
        
    def addlineno(self, lineno):
        self.lineno = lineno
        return self

class body(node): pass
class expr(body): pass

class program(node):
    def __init__(self, defns):
        self.defns = defns
    
    def __repr__(self):
        return "program(%r)" % self.defns  

class functionDef(node):
    def __init__(self, name, formals, type, body):
        self.name = name
        self.formals = formals
        self.type = type
        self.body = body
    
    def __repr__(self):
        return "functionDef(%r, %r, %r)" % (self.name, self.formals, self.body)

class formals(node):
    def __init__(self, params):
        self.params = params
    
    def __repr__(self):
        return "formals(%r)" % self.params

class actuals(node):
    def __init__(self, params):
        self.params = params
    
    def __repr__(self):
        return "actuals(%r)" % self.params

class typename(node):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return "typename(%r)" % self.name

class printBody(body):
    def __init__(self, actuals, rest):
        self.actuals = actuals
        self.rest = rest
    
    def __repr__(self):
        return "printBody(%r, %r)" % (self.actuals, self.rest)

class binaryExpr(expr):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    
    def __repr__(self):
        return "binaryExpr(%r, %r, %r)" % (self.left, self.operator, self.right)
        
class ifExpr(expr):
    def __init__(self, condExpr, thenExpr, elseExpr):
        self.condExpr = condExpr
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr
    
    def __repr__(self):
        return "ifExpr(%r, %r, %r)" % (self.condExpr, self.thenExpr, self.elseExpr)
    
class notExpr(expr):
    def __init__(self, expr):
        self.expr = expr
    
    def __repr__(self):
        return "notExpr(%r)" % self.expr

class functionCall(expr):
    def __init__(self, name, actuals):
        self.name = name
        self.actuals = actuals
    
    def __repr__(self):
        return "functionCall(%r, %r)" % (self.name, self.actuals)

class identifier(expr):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return "identifier(%r)" % self.value


class integerlit(expr):
    def __init__(self, value):
        self.value = int(value)
    
    def __repr__(self):
        return "integerlit(%s)" % self.value 

class booleanlit(expr):
    def __init__(self, value):
        if value == 'true':
            self.value = True
        else:
            self.value = False
    
    def __repr__(self):
        return "booleanlit(%s)" % ("true" if self.value else "false")
