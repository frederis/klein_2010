import ast
class prettyPrinter(object):
    def display(self, str, depth):
        print '  '*depth + str
        
    def visit_program(self, program, depth):
        self.display('program', depth)
        for defn in program.defns:
            defn.accept(self, depth+1)
    
    def visit_printBody(self, printBody, depth):
        self.display('printBody', depth)
        printBody.actuals.accept(self, depth+1)
        printBody.rest.accept(self, depth+1)
    
    def visit_functionDef(self, functionDef, depth):
        self.display('functionDef', depth)
        functionDef.name.accept(self, depth+1)
        functionDef.formals.accept(self, depth+1)
        functionDef.type.accept(self, depth+1)
        functionDef.body.accept(self, depth+1)
    
    def visit_formals(self, formals, depth):
        self.display('formals', depth)
        for (name, type) in formals.params:
            name.accept(self, depth+1)
            type.accept(self, depth+1)
            
    def visit_actuals(self, actuals, depth):
        self.display('actuals', depth)
        for name in actuals.params:
            name.accept(self, depth+1)

    def visit_typename(self, typename, depth):
        self.display(str(typename), depth)
    
    def visit_binaryExpr(self, binaryExpr, depth):
        self.display('binaryExpr(%r)' % binaryExpr.operator, depth)
        binaryExpr.left.accept(self, depth+1)
        binaryExpr.right.accept(self, depth+1)
    
    def visit_ifExpr(self, ifExpr, depth):
        self.display('ifExpr', depth)
        ifExpr.condExpr.accept(self, depth+1)
        ifExpr.thenExpr.accept(self, depth+1)
        ifExpr.elseExpr.accept(self, depth+1)
    
    def visit_functionCall(self, functionCall, depth):
        self.display('functionCall', depth)
        functionCall.name.accept(self, depth+1)
        functionCall.actuals.accept(self, depth+1)
    
    def visit_identifier(self, identifier, depth):
        self.display(str(identifier), depth)
    
    def visit_integerlit(self, integerlit, depth):
        self.display(str(integerlit), depth)
        
    def visit_booleanlit(self, booleanlit, depth):
        self.display(str(booleanlit), depth)
    
    def visit_notExpr(self, notExpr, depth):
        self.display('notExpr', depth)
        notExpr.expr.accept(self, depth+1)
    

def prettyPrint(ast):
    ast.accept(prettyPrinter(), 0)