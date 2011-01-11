#!/usr/bin/env python

import sys
import parser
import pretty_print
import kleinTypes
import symboltable
import codegen

def main():
    code = sys.stdin.read()
    table = symboltable.SymbolTable()
    try:
        ast = parser.parse(code)
        errors = kleinTypes.check(ast, table)
        if not errors:
            errors = table.check()
        if errors:
            for error in errors:
                print >> sys.stderr, error
        else:
            codegen.compile(ast, table)
    
    except SyntaxError, e:
        print >> sys.stderr, "Syntax Error:", e
    except symboltable.SemanticError, e:
        print >> sys.stderr, e

if __name__ == '__main__':
    main()
