import ast
class visitor(object):
    """
    Convert the AST into three address code.
    """
    def __init__(self):
        self.program = []
        self.functions = {}
        self.scope = {}
        self.printLabel = label()

    def visit_program(self, program): # done
        # build up function labels
        for defn in program.defns:
            self.functions[defn.name.value] = label()
        # generate system code
        self.program.append(system(self.functions['main'], self.printLabel))
        # generate program code
        for defn in program.defns:
            if defn.name.value == 'main':
                defn.accept(self)
                break
        for defn in program.defns:
            if defn.name.value != 'main':
                defn.accept(self)
    
    def visit_printBody(self, printBody): # done
        numargs = var()
        target = var()
        self.program.append(literal(numargs, len(printBody.actuals.params)))
        args = [numargs]
        for actual in printBody.actuals.params:
            args.append(actual.accept(self))
        self.program.append(reserve(target))
        for val in args:
            self.program.append(push(val))
        self.program.append(call(target, self.printLabel))
        return printBody.rest.accept(self)
    
    def visit_functionDef(self, defn): # done
        self.program.append(self.functions[defn.name.value])
        self.program.append(entry(defn.name.value, len(defn.formals.params)))
        self.scope = {}
        for i, formal in enumerate(defn.formals.params):
            self.scope[formal[0].value] = i
        val = defn.body.accept(self)
        self.program.append(retrn(val))
        self.program.append(exit(defn.name.value))
        
    
    def visit_binaryExpr(self, binaryExpr): # done
        target = var()
        if binaryExpr.operator == tokens.AND:
            thenlabel = label()
            endlabel = label()
            
            left = binaryExpr.left.accept(self)
            self.program.append(jif(left, thenlabel))
            
            self.program.append(literal(target, 0))
            self.program.append(jump(endlabel))

            self.program.append(thenlabel)
            right = binaryExpr.right.accept(self)
            self.program.append(assignment(target, right))

            self.program.append(endlabel)
            
            return target
        if binaryExpr.operator == tokens.OR:
            thenlabel = label()
            endlabel = label()
            
            left = binaryExpr.left.accept(self)
            self.program.append(jif(left, thenlabel))
            
            right = binaryExpr.right.accept(self)
            self.program.append(assignment(target, right))
            self.program.append(jump(endlabel))

            self.program.append(thenlabel)
            self.program.append(literal(target, 1))

            self.program.append(endlabel)
            
            return target
        left   = binaryExpr.left.accept(self)
        right  = binaryExpr.right.accept(self)
        self.program.append(binary(target, left, binaryExpr.operator, right))
        return target
        
    
    def visit_ifExpr(self, ifExpr): # done
        thenLabel = label()
        endifLabel = label()
        target = var()
        
        condVar = ifExpr.condExpr.accept(self)
        self.program.append(jif(condVar, thenLabel))
        
        elseVal = ifExpr.elseExpr.accept(self)
        self.program.append(assignment(target, elseVal))
        self.program.append(jump(endifLabel))
        
        self.program.append(thenLabel)
        thenVal = ifExpr.thenExpr.accept(self)
        self.program.append(assignment(target, thenVal))

        self.program.append(endifLabel)
        return target
        
    
    def visit_functionCall(self, functionCall): # done
        args = []
        target = var()
        for actual in functionCall.actuals.params:
            args.append (actual.accept(self))
        self.program.append(reserve(target))
        for val in args:
            self.program.append(push(val))
        label = self.functions[functionCall.name.value]
        self.program.append(call(target, label))
        return target
        
    
    def visit_identifier(self, identifier): # done
        target = var()
        self.program.append(
            argument(target, self.scope[identifier.value])
        )
        return target
        
    
    def visit_integerlit(self, integerlit): # done
        target = var()
        self.program.append(literal(target, integerlit.value))
        return target
    
    def visit_booleanlit(self, booleanlit): # done
        target = var()
        self.program.append(literal(target, 1 if booleanlit.value else 0))
        return target
    
    def visit_notExpr(self, notExpr): # done
        arg = notExpr.expr.accept(self)
        target = var()
        self.program.append(notexpr(target, arg))
        return target



def convert(ast):
    """Convert an AST into Three Address Code."""
    v = visitor()
    ast.accept(v)
    return v.program
        
        
numvars = 0
def var():
    """Generate a new variable id."""
    global numvars
    numvars += 1
    return numvars


    
def compile(ast, table):
    global _table
    _table = table
    program = convert(ast)
    for line in program:
        line.compile()
    
# ####
# Helper classes 
# ###
import tokens
import emit
import random
SP = 0
PC = emit.PC
freeregs = range(1,7)

class stack(object):
    def __init__(self, nargs):
        self.nargs = nargs
        self.vals = []
    
    def offsetReturn(self):
        return 0
        
    def offsetArg(self, n):
        if n >= self.nargs:
            raise ValueError, "kill yourself etc"
        return n+1
        
    def offsetReturnAddr(self):
        return self.nargs+1
    
    def offsetProgState(self,i=0):
        return self.nargs+2+i
        
    def restoreProgState(self):
        for i,r in enumerate(freeregs):
            emit.RM("LD", r, self.offsetProgState(i), SP)
    
    def writeProgState(self):
        for i,r in enumerate(freeregs):
            emit.RM("ST", r, self.offsetProgState(i), SP)
    
    def offsetTemp(self, n=0):
        return self.nargs+8+n
    
    def __len__(self):
        return len(self.vals)
    
    def push(self, var):
        self.vals.append(var)
        return self.offsetTemp(len(self)-1)
    
    def pop(self):
        return self.vals.pop()
    
    def offsetVar(self, var):
        try:
            index = self.vals.index(var)
            if index == -1:
                return None
            else:
                return self.offsetTemp(index)
        except ValueError:
            return None
    
    def freeVar(self, var):
        try:
            index = self.vals.index(var)
            self.vals[index] = 0
        except ValueError:
            pass
    
    def emitLD(self, target, offset, comment=None, location=None):
        emit.RM("LD",  target, offset, SP, comment, location)
    def emitLDA(self, target, offset, comment=None, location=None):
        emit.RM("LDA", target, offset, SP, comment, location)
    def emitST(self, target, offset, comment=None, location=None):
        emit.RM("ST",  target, offset, SP, comment, location)


class registers(object):
    def __init__(self):
        self.map = {}
        self.order = []
        for i in freeregs: self.map[i] = 0    
    
    def allocate(self, var):
        for i in freeregs:
            if self.map[i] == 0:
                self.map[i] = var
                return i
                
        i = self.order.pop(0)
        offset = _stack.push(self.map[i])
        emit.RM("ST", i, offset, SP)
        self.map[i] = var
        return i
    
    def need(self, var):
        for i in freeregs:
            if self.map[i] == var:
                if i in self.order:
                    del self.order[self.order.index(i)]
                self.order.append(i)
                return i
                
        i = self.allocate(var)
        offset = _stack.offsetVar(var)
        if offset is not None:
            emit.RM("LD", i, offset, SP, "restoring register")
        if i in self.order:
            del self.order[self.order.index(i)]
        self.order.append(i)
        return i
        
    
    def freeReg(self, var):
        if var in self.map:
            _stack.freeVar(self.map[var])
        self.map[var] = 0
        if var in self.order:
            del self.order[self.order.index(var)]
    
_stack     = None
_registers = None
_nextFrame = None

    
# ############
# Three Address Code
# ############
class tac(object): pass

class assignment(tac):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def __repr__(self):
        return "assignment(%r, %r)" % (self.left, self.right)
    
    def compile(self):
        rightr = _registers.need(self.right)
        leftr  = _registers.need(self.left)
        emit.RM("LDA", leftr, 0, rightr, repr(self))
        _registers.freeReg(rightr)
    

class notexpr(tac):
    def __init__(self, target, arg):
        self.target = target
        self.arg = arg
    
    def __repr__(self):
        return "notexpr(%r, %r)" % (self.target, self.arg)

    def compile(self):
        targetr = _registers.need(self.target)
        argr    = _registers.need(self.arg)
        oner    = _registers.need(var())
        emit.RM("LDC", oner,  1,    0, repr(self))
        emit.RO("SUB", targetr, oner, argr)
        _registers.freeReg(argr)
        _registers.freeReg(oner)
    
        
class binary(tac):
    def __init__(self, target, left, op, right):
        self.target = target
        self.left = left
        self.op = op
        self.right = right
    
    def __repr__(self):
        return "binary(%r, %r, %r, %r)" % (self.target, self.left, self.op, self.right)
    
    def compile(self):
        leftr   = _registers.need(self.left)
        rightr  = _registers.need(self.right)
        targetr = _registers.need(self.target)
        if self.op == tokens.PLUS:
            emit.RO("ADD", targetr, leftr, rightr, repr(self))
        elif self.op == tokens.MINUS:
            emit.RO("SUB", targetr, leftr, rightr, repr(self))
        elif self.op == tokens.STAR:
            emit.RO("MUL", targetr, leftr, rightr, repr(self))
        elif self.op == tokens.DIVIDE:
            emit.RO("DIV", targetr, leftr, rightr, repr(self))
        elif self.op == tokens.AND:
            emit.RO("MUL", targetr, leftr, rightr, repr(self))
        elif self.op == tokens.OR:
            tempr = _registers.need(var())
            emit.RO("ADD", targetr, leftr, rightr, repr(self))
            emit.RM("LDA", targetr, 1, targetr)
            emit.RM("LDC", tempr, 2, 0)
            emit.RO("DIV", targetr, targetr, tempr)
            _registers.freeReg(tempr)
        elif self.op == tokens.EQUALS:
            emit.RO("SUB", targetr, leftr, rightr, repr(self))
            emit.RM("JEQ", targetr, 2, PC)
            emit.RM("LDC", targetr, 0, 0)
            emit.RM("LDA", PC, 1, PC)
            emit.RM("LDC", targetr, 1, 0)       
        elif self.op == tokens.LANGLE:
            emit.RO("SUB", targetr, leftr, rightr, repr(self))
            emit.RM("JLT", targetr, 2, PC)
            emit.RM("LDC", targetr, 0, 0)
            emit.RM("LDA", PC, 1, PC)
            emit.RM("LDC", targetr, 1, 0)       
        else:
            raise ValueError, "what is this operator? %s" % self.op
        _registers.freeReg(leftr)
        _registers.freeReg(rightr)
        
    
    
class reserve(tac):
    """reserve space on stack for return value"""
    def __init__(self, target):
        self.target = target
    
    def __repr__(self):
        return "reserve(%d)" % self.target
    
    def compile(self):
        global _nextFrame
        global _targetr
        _targetr = _registers.need(self.target)
        _registers.freeReg(_registers.need(var())) # need an open register
        _nextFrame = _stack.offsetTemp(len(_stack))
        _stack.push(0)
        
class push(tac):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return "push(%r)" % self.value
    
    def compile(self):
        valuer = _registers.need(self.value)
        offset = _stack.push(self.value)
        emit.RM("ST", valuer, offset, SP, repr(self))
        _registers.freeReg(valuer)
        
        
class call(tac):
    def __init__(self, target, label):
        self.target = target
        self.label  = label
    
    def __repr__(self):
        return "call(%r, %r)" % (self.target, self.label)
    
    def compile(self):
        RAoffset = _stack.push(0)
        
        # calling sequence, before call
        emit.RM("LDA", _targetr, 3, PC, repr(self))
        emit.RM("ST", _targetr, RAoffset, SP)
        emit.RM("LDA", SP,  _nextFrame, SP)
        self.label.produce(
            lambda origin, target:
                emit.RMAbs("LDA", PC, target, None, origin)
        )
        emit.skip()
        
        # calling sequence, after call
        emit.RM("LD",  _targetr, 0, SP)
        emit.RM("LDA", SP, -_nextFrame, SP)
        
    
class retrn(tac):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return "retrn(%r)" % self.value

    def compile(self):
        valuer = _registers.need(self.value)
        emit.RM("ST", valuer, _stack.offsetReturn(), SP, repr(self))
        _stack.restoreProgState()
        emit.RM("LD", PC, _stack.offsetReturnAddr(), SP)
    
class entry(tac):
    def __init__(self, name, nargs):
        self.name = name
        self.nargs = nargs
    
    def __repr__(self):
        return "entry(%r)" % self.name
    
    def compile(self):
        emit.comment(repr(self))
        global _stack, _registers
        _stack = stack(self.nargs)
        _stack.writeProgState()
        _registers = registers()
        
class argument(tac):
    def __init__(self, target, position):
        self.target = target
        self.position = position
    
    def __repr__(self):
        return "argument(%r, %r)" % (self.target, self.position)
    
    def compile(self):
        targetr = _registers.need(self.target)
        emit.RM("LD", targetr, _stack.offsetArg(self.position), SP, repr(self))

class exit(tac):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return "exit(%r)" % self.name
    
    def compile(self):
        emit.comment(repr(self))

class jif(tac):
    def __init__(self, cond, label):
        self.cond = cond
        self.label = label
    
    def __repr__(self):
        return "jif(%r, %r)" % (self.cond, self.label)
    
    def compile(self):
        condr = _registers.need(self.cond)
        self.label.produce(
            lambda origin, target:
                emit.RMAbs("JNE", condr, target, repr(self), origin)
        )
        emit.skip()
        _registers.freeReg(condr)
        
class jump(tac):
    def __init__(self, label):
        self.label = label
     
    def __repr__(self):
        return "jump(%r)" % self.label
    
    def compile(self):
        self.label.produce(
            lambda origin, target:
                emit.RMAbs("LDA", PC, target, repr(self), origin)
        )
        emit.skip()
        
class label(tac):
    def __init__(self):
        self.id = var()
        self.fns = []
        self.location = None
    
    def __repr__(self):
        return "label(%r)" % self.id
    
    def produce(self, fn):
        if self.location is None:
            self.fns.append((fn, emit.location()))
        else:
            fn(emit.location(), self.location)
    
    def compile(self):
        emit.comment(repr(self))
        self.location = emit.location()
        for fn, origin in self.fns:
            fn(origin, self.location)
        del self.fns
    
class literal(tac):
    def __init__(self, target, value):
        self.target = target
        self.value = value
        
    def __repr__(self):
        return "literal(%r, %r)" % (self.target, self.value)
     
    def compile(self):
        targetr = _registers.need(self.target)
        emit.RM("LDC", targetr, self.value, 0, repr(self))



class system(tac):
    def __init__(self, mainLabel, printLabel):
        self.mainLabel = mainLabel
        self.printLabel = printLabel
    
    def __repr__(self):
        return "system(%r, %r)" % (self.mainLabel, self.printLabel)
    
    def compile(self):
        emit.comment("system code")
        emit.RM("LDC", SP, 0, 0)
        emit.RM("LDA", 1, 2, PC)
        emit.RM("ST", 1, 1+_table.nargs("main"), SP)
        self.mainLabel.produce(
            lambda origin, target:
                emit.RMAbs("LDA", PC, target, "jump to main", origin)
        )
        emit.skip()
        
        emit.RM("LD", 1, 0, SP)
        emit.RO("OUT", 1, 0,0)
        emit.RO("HALT", 0,0,0, "done.")
        
        emit.comment("print function")
        self.printLabel.compile()
        
        emit.RM("LD", 1, 1, SP)
        emit.RM("LDA", 2, 2, SP)
        
        emit.RM("LD",  3, 0, 2)
        emit.RO("OUT", 3, 0, 0)
        emit.RM("LDA", 2, 1, 2)
        emit.RM("LDA", 1, -1, 1)
        emit.RM("JNE", 1, -5, 7)
        
        emit.RM("LD", 1, 1, SP)
        emit.RO("ADD", 1, 1, SP)
        emit.RM("LD", 7,  2, 1)
        
        emit.comment("program code")
