import ast

class kleinType(object):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    
integer = kleinType('integer')
boolean = kleinType('boolean')

class function(kleinType):
    def __init__(self, formals, returnType):
        self.formals = formals
        self.returnType = returnType
        
    def __repr__(self):
        return "function(%r, %r)"  % (self.formals, self.returnType)
    

def convertTypename(typename):
    return {'integer': integer, 'boolean': boolean}[typename.name]

# Type checker

import tokens

operatorTypes = {
    'PLUS': function((integer, integer), integer),
    'MINUS': function((integer, integer), integer),
    'STAR': function((integer, integer), integer),
    'DIVIDE': function((integer, integer), integer),
    'LANGLE': function((integer, integer), boolean),
    'OR': function((boolean, boolean), boolean),
    'AND': function((boolean, boolean), boolean),
}

class typeChecker(object):
    def __init__(self, table):
        self.table = table
        self.errors = []
    
    def addError(self, msg, lineno=None):
        self.errors.append(msg + " (line %s)" % lineno if lineno else msg)
    
    def expect(self, got, expected, fnname=None, msg=None):
        lineno = None
        if isinstance(got, ast.node):
            lineno = got.lineno
            got = got.accept(self, fnname)
        if isinstance(expected, ast.node):
            if not lineno: lineno = expected.lineno
            expected = expected.accept(self, fnname)
            
        if got and expected and got != expected:
            if msg == None:
                msg = "expected %r got %r" % (expected, got)
            self.addError(msg, lineno)
        else:
            return got
    
    def visit_program(self, program):
        for functionDef in program.defns:
            formalTypes = map(
                lambda f: convertTypename(f[1]),
                functionDef.formals.params
            )
            returnType = convertTypename(functionDef.type)
            fnType = function(formalTypes, returnType)
            self.table.functionDefinition(
                functionDef.name.value,
                fnType,
                functionDef.name.lineno
            )
        for functionDef in program.defns:
            functionDef.accept(self)
    
    def visit_functionDef(self, functionDef):
        for formal in functionDef.formals.params:
            self.table.symbolDefinition(
                functionDef.name.value,
                formal[0].value,
                convertTypename(formal[1]),
                formal[0].lineno
            )
        self.expect(
            functionDef.body,
            convertTypename(functionDef.type),
            functionDef.name.value
        )
    
    def visit_printBody(self, printBody, fnname):
        for actual in printBody.actuals.params:
            actual.accept(self, fnname)
        return printBody.rest.accept(self, fnname)
    
    def visit_binaryExpr(self, binaryExpr, fnname):
        if binaryExpr.operator == tokens.EQUALS:
            self.expect(binaryExpr.left, binaryExpr.right, fnname, "conflicting types for equality comparison")
            return boolean
        else:
            optype = operatorTypes[binaryExpr.operator.name]
            self.expect(binaryExpr.left, optype.formals[0], fnname)
            self.expect(binaryExpr.right, optype.formals[1], fnname)
            return optype.returnType
    
    def visit_ifExpr(self, ifExpr, fnname):
        self.expect(ifExpr.condExpr, boolean, fnname)
        return self.expect(
            ifExpr.thenExpr,
            ifExpr.elseExpr,
            fnname,
            "conflicting types for branches of if expression"
        )
    

    def visit_functionCall(self, functionCall, fnname):
        fnType = self.table.functionReference(
            functionCall.name.value,
            functionCall.lineno
        )
        if not fnType:
            self.addError(
                "function not defined: %s" % functionCall.name.value,
                functionCall.name.lineno
            )
            fnType = function([None]*len(functionCall.actuals.params), None)
        if len(fnType.formals) != len(functionCall.actuals.params):
            self.errors.append(
                "%s expected %s parameters, got %s parameters (line %s)" % (
                    functionCall.name.value,
                    len(fnType.formals),
                    len(functionCall.actuals.params),
                    functionCall.lineno
                )
            )
        for i in xrange(min(len(fnType.formals),
                            len(functionCall.actuals.params))):
            self.expect(
                functionCall.actuals.params[i],
                fnType.formals[i],
                fnname
            )
        return fnType.returnType

    def visit_identifier(self, identifier, fnname):
        idtype = self.table.symbolReference(
            fnname,
            identifier.value,
            identifier.lineno
        )
        if not idtype:
            self.addError(
                "identifier not defined: %s" % identifier.value,
                identifier.lineno
            )
        return idtype
     
    def visit_integerlit(self, integerlit, fnname):
        return integer
        
    def visit_booleanlit(self, booleanlit, fnname):
        return boolean
        
    def visit_notExpr(self, notExpr, fnname):
        return self.expect(notExpr.expr, boolean, fnname)
        
    
def check(expr, table):
    checker = typeChecker(table)
    expr.accept(checker)
    return checker.errors
