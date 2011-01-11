
_location = 0
trace = True
PC = 7

def comment(comment):
    if trace:
        print "*", comment

def RO(op, target, source1, source2, comment=None, location=None):
    """
    emit.RO(op, target, source1, source2, comment=None, location=None)
    Emit a register-only TM instruction.
    """
    if location is None:
        global _location
        location = _location
        _location += 1
    print "%d: %5s  %d,%d,%d" % (location, op, target, source1, source2),
    if trace and comment:
        print "\t", comment
    else:
        print
    
def RM(op, target, offset, base, comment=None, location=None):
    """
    emit.RM(op, target, offset, base, comment=None, location=None)
    Emit a register-memory instruction.
    """
    if location is None:
        global _location
        location = _location
        _location += 1
    print "%d: %5s  %d,%d(%d)" % (location, op, target, offset, base),
    if trace and comment:
        print "\t", comment
    else:
        print

def RMAbs(op, target, absolute, comment=None, location=None):
    """
    emit.RMAbs(op, target, absolute, comment=None, location=None)
    Emit a register-memory instruction with an absolute address.
    """
    if location is None:
        global _location
        location = _location
        _location += 1
    print "%d: %5s  %d,%d(%d)" % (location, op, target, absolute-(location+1), PC),
    if trace and comment:
        print "\t", comment
    else:
        print

def skip(n=1):
    global _location
    oldlocation = _location
    _location += n
    return oldlocation

def location():
    return _location