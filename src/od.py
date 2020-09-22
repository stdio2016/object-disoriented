import argparse
import sys

args = argparse.ArgumentParser()
args.add_argument('file', help='Object Disoriented program')
args = args.parse_args()

namescope = ['', 0]
klasses = {}

class Scanner:
    def __init__(self, file):
        self.file = file
        self.line = ''
        self.lineno = 0
        self.pos = 0
    def next(self):
        if self.pos == len(self.line):
            self.pos = 0
            self.line = self.file.readline()
            self.lineno += 1
        self.pos += 1
        if self.line == '':
            return ''
        return self.line[self.pos-1]
    def readToDot(self):
        i = self.line.find('.', self.pos)
        ans = self.line[self.pos:i]
        while i == -1:
            self.pos = 0
            self.lineno += 1
            self.line = self.file.readline()
            if self.line == '':
                return None
            i = self.line.find('.')
            ans += self.line[0:i]
        self.pos = i+1
        return ans

class Klass:
    def __init__(self, code, a, b, name):
        self.code = code
        self.a = a
        self.b = b
        self.name = name
    def __repr__(self):
        return "<class %s>" % self.name

class Zero:
    def __init__(self):
        self.flip = 0
    def own(self):
        return 0
    def incrOwn(self):
        pass
    def decrOwn(self):
        pass
    def vis(self):
        return 0
    def incrVis(self):
        pass
    def decrVis(self):
        pass
    def isDirty(self):
        return False
    def copy(self):
        return self
    def __repr__(self):
        return 'z'
zero = Zero()
onetest = Zero()

class Ref:
    def __init__(self, o, tmp=True):
        self.o = o
        self.tmp = tmp
        if not tmp:
            o.incrOwn()
    def take(self):
        # lvalue
        if self.o.own() > 1:
            assert self.o.vis() == 0, 'visss'
            # copy myself
            self.o.decrOwn()
            self.o = Obj(self.o.a.o, self.o.b.o, self.o.f)
            self.o.incrOwn()
        self.o.incrVis()
        return self
    def untake(self):
        # pop from stack
        self.o.decrVis()
    def setTo(self, p):
        # c command
        self.o.decrVis()
        if not self.tmp:
            self.o.decrOwn()
        self.o = p.o.copy()
        if not self.tmp:
            self.o.incrOwn()
        p.untake()
    def __repr__(self):
        return '&'+str(self.o)

class Obj:
    def __init__(self, a, b, f):
        self.a = Ref(a, False)
        self.b = Ref(b, False)
        self.f = f
        self._dirty = False
        self._own = 0
        self._vis = 0
    def __del__(self):
        #print(self.f.name, self.vis(), self.own())
        pass
    def own(self):
        return self._own
    def incrOwn(self):
        self._own += 1
    def decrOwn(self):
        self._own -= 1
        if self._own + self._vis == 0:
            self.a.o.decrOwn()
            self.b.o.decrOwn()
    def vis(self):
        return self._vis
    def incrVis(self):
        self._vis += 1
        self._dirty = True
    def decrVis(self):
        self._vis -= 1
        if self._own + self._vis == 0:
            self.a.o.decrOwn()
            self.b.o.decrOwn()
    def isDirty(self):
        return self._dirty
    def copy(self):
        if self._dirty:
            a = self.a.o
            a2 = a.copy()
            b = self.b.o
            b2 = b.copy()
            self._dirty = self._vis > 0 or a.isDirty() or b.isDirty()
            return Obj(a2, b2, self.f)
        return self
    def __repr__(self):
        return "%x{a=%s b=%s f=%s vis=%d own=%d dirty=%s}"%(
            hash(self), self.a, self.b, self.f, self._vis, self._own, self._dirty
        )

def createObject(a, b, klass):
    out = Ref(Obj(a.o.copy(), b.o.copy(), klass)).take()
    a.untake()
    b.untake()
    return out

bitbuffer = [0, 0]
def outputBit(bit):
    bitbuffer[0] = bitbuffer[0]*2 + bit
    bitbuffer[1] += 1
    if bitbuffer[1] == 8:
        bitbuffer[1] = 0
        sys.stdout.write(chr(bitbuffer[0]))
        bitbuffer[0] = 0

klasses['.one'] = Klass(['p', 'z', 'f', '*', 'z'], [], [], '.one')
inbitbuffer = [0, 0]
def inputBit():
    if inbitbuffer[1] == 0:
        c = sys.stdin.read(1)
        if c == '':
            inbitbuffer[0] = 0
        else:
            inbitbuffer[0] = ord(c)
        inbitbuffer[1] = 8
    inbitbuffer[1] -= 1
    return (inbitbuffer[0] >> inbitbuffer[1]) & 1

def runFunc(s, p):
    self = s.o
    if self is zero:
        p.untake()
        return s
    if self is onetest:
        p.untake()
        onetest.flip = 1 - onetest.flip
        return s
    #print('enter', self.f.name)
    self.incrVis()
    t = Ref(zero, False)
    stack = []
    for op in self.f.code:
        if op == 'f':
            p0 = stack.pop()
            s0 = stack.pop()
            stack.append(runFunc(s0, p0))
        elif op == 'z':
            stack.append(Ref(zero))
        elif op == 'a':
            stack.append(self.a.take())
        elif op == 'b':
            stack.append(self.b.take())
        elif op == 'p':
            stack.append(p.take())
        elif op == 's':
            stack.append(s.take())
        elif op == 't':
            stack.append(t.take())
        elif op == 'c':
            ddest = stack.pop()
            ssrc = stack.pop()
            ddest.setTo(ssrc)
        elif op == '*':
            stack.pop().untake()
        elif op == '?':
            print(stack[-1])
        elif op == 'o':
            what = stack.pop()
            onetest.flip = 0
            runFunc(what, Ref(onetest)).untake()
            outputBit(onetest.flip)
        elif op == 'i':
            if inputBit() == 0:
                stack.append(Ref(zero))
            else:
                stack.append(createObject(Ref(zero), Ref(zero), klasses['.one']))
        elif isinstance(op, Klass):
            b = stack.pop()
            a = stack.pop()
            stack.append(createObject(a, b, op))
        else:
            raise NotImplementedError(op)
    # release object
    self.decrVis()
    p.untake()
    s.untake()
    t.o.decrOwn()
    #print('leave', self.f.name)
    return stack[0]

def parseExpr(s, code, stmt=False):
    while True:
        ch = s.next()
        if ch == '':
            raise SyntaxError('Expected expression',
                (args.file, s.lineno, s.pos, s.line))
        if ord(ch) <= 32:
            pass
        elif ch == 'e':
            if s.readToDot() is None:
                raise SyntaxError('Missing end of class name',
                    (args.file, s.lineno, s.pos, s.line))
        else:
            break
    if ch in 'abpstzi':
        code.append(ch)
    elif ch == 'f':
        # function call: f**
        parseExpr(s, code)
        parseExpr(s, code)
        code.append('f')
    elif ch == 'l':
        # l"id".
        # create a new instance of class "id"
        myname = s.readToDot()
        if myname is None:
            raise SyntaxError('Missing end of class name',
                (args.file, s.lineno, s.pos, s.line))
        code.append('l'+myname)
    elif ch == 'n':
        inner = []
        namescope[-1] += 1
        namescope.append(0)
        while parseExpr(s, inner, True):
            pass
        namescope.pop()
        parseExpr(s, code)
        parseExpr(s, code)
        genname = '.'.join(str(x) for x in namescope)
        kls = Klass(inner, [], [], genname)
        klasses[genname] = kls
        code.append(kls)
    elif ch == '?':
        parseExpr(s, code)
        code.append('?')
    elif stmt and ch == 'c':
        parseExpr(s, code)
        parseExpr(s, code)
        code.append('c')
    elif stmt and ch in 'or':
        parseExpr(s, code)
        if ch == 'r':
            return False
        code.append(ch)
    else:
        raise SyntaxError('Unknown character: %c' % ch,
            (args.file, s.lineno, s.pos, s.line))
    if stmt and ch not in 'cor':
        code.append('*')
    return True

def parse(s):
    inname = False
    while True:
        ch = s.next()
        if ch == '': break
        if ord(ch) <= 32:
            pass
        elif ch == 'd':
            lineno, pos, line = s.lineno, s.pos, s.line
            name = s.readToDot()
            if name is None:
                raise SyntaxError('Missing end of class name',
                    (args.file, s.lineno, s.pos, s.line))
            if name in klasses:
                raise SyntaxError("Class '%s' is redeclared"%name,
                    (args.file, lineno, pos, line))
            code = []
            namescope[0] = name
            namescope[1] = 0
            while parseExpr(s, code, True):
                pass
            a = []
            parseExpr(s, a)
            b = []
            parseExpr(s, b)
            klass = Klass(code, a, b, name)
            klasses[name] = klass
        elif ch == 'e':
            if s.readToDot() is None:
                raise SyntaxError('Missing end of class name',
                    (args.file, s.lineno, s.pos, s.line))
        else:
            raise SyntaxError('Unknown character: %c' % ch,
                (args.file, s.lineno, s.pos, s.line))
    return klasses

with open(args.file, encoding='utf-8') as fin:
    s = Scanner(fin)
    klasses = parse(s)

# replace 1"id". with actual classes
for name in klasses:
    cls = klasses[name]
    newcode = []
    for op in cls.code:
        if isinstance(op, str) and op[0] == 'l':
            ref = klasses[op[1:]]
            newcode += ref.a
            newcode += ref.b
            newcode.append(ref)
        else:
            newcode.append(op)
    cls.code = newcode
    #print(cls, cls.code)

main_class = klasses['main']
main0_code = main_class.a + main_class.b + [main_class, 'z', 'f']
main0_class = Klass(main0_code, ['z'], ['z'], '.main')
main0 = Ref(Obj(zero, zero, main0_class))
main0.take()
runFunc(main0, Ref(zero))
