class SemanticError(Exception):
    pass
    
# Symbol Table Entry
class Entry(object):
    def __init__(self, name, kleinType, lineno):
        self.name = name
        self.type = kleinType
        self.lineno = lineno
        self.symbols = {}
        self.references = []
    
    def definition(self, name, kleinType, lineno):
        if name in self.symbols:
            raise SemanticError, "Duplicate symbol definition for %s" % name
        self.symbols[name] = Entry(name, kleinType, lineno)
    
    def reference(self, name, lineno):
        if name not in self.symbols:
            return None
            raise SemanticError, "No such symbol: %s" % name
        self.symbols[name].addReference(lineno)
        return self.symbols[name].type
    
    def addReference(self, lineno):
        self.references.append(lineno)
    
    def outputLines(self, fnname=None):
        lines = []
        lines.append("%s : %s" % (self.name, self.type))
        if fnname:
            lines.append("    defined on line %s, in %s" % (self.lineno, fnname))
        else:
            lines.append("    defined on line %s" % self.lineno)
        for reference in self.references:
            lines.append("    referenced on line %s" % reference)
        return lines
    
    def output(self, fnname=None):
        for line in self.outputLines(fnname):
            print line
    
 
# Symbol Table for Program
class SymbolTable(object):
    def __init__(self):
        self.functions = {}
    
    def functionDefinition(self, name, kleinType, lineno):
        if name in self.functions:
            raise SemanticError, "Duplicate function definition for %s" % name 
        self.functions[name] = Entry(name, kleinType, lineno)
    
    def functionReference(self, name, lineno):
        if name not in self.functions:
            return None
            raise SemanticError, "No such function: %s" % name
        self.functions[name].addReference(lineno)
        return self.functions[name].type
    
    def functionType(self, name):
        return self.functions[name].type
    
    def symbolDefinition(self, fnname, name, kleinType, lineno):
        self.functions[fnname].definition(name, kleinType, lineno)
    
    def symbolReference(self, fnname, name, lineno):
        return self.functions[fnname].reference(name, lineno)
    
    def symbolType(self, fnname, name):
        return self.functions[fnname].symbols[name].type
    
    def output(self):
        symbolLines = {}
        for name in self.functions:
            self.functions[name].output()
            for symbol in self.functions[name].symbols:
                lines = self.functions[name].symbols[symbol].outputLines(name)
                if symbol in symbolLines:
                    symbolLines[symbol][0] = symbol
                    symbolLines[symbol].extend(lines[1:])
                else:
                    symbolLines[symbol] = lines
            print
        for symbol in symbolLines:
            for line in symbolLines[symbol]:
                print line
            print
    
    def nargs(self, name):
        return len(self.functions[name].type.formals)
    
    def check(self):
        # Run semantic checks
        errors = []
        if 'main' not in self.functions:
            errors.append("main function not defined")
        return errors