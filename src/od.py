import argparse

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
    def __init(self):
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

class Ref:
    def __init__(self, o, tmp=True):
        self.o = o
        self.tmp = tmp
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
        if self.tmp and self.o.vis() == 0:
            self.o.decrOwn()
    def setTo(self, p):
        # c command
        self.o.decrVis()
        self.o.decrOwn()
        self.o = p.o.copy()
        self.o.incrOwn()
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
    return Ref(Obj(a.o.copy(), b.o.copy(), klass)).take()

t = Ref(zero, False)
t.take()
t.take()
t.take()
t.untake()
t.untake()
t1 = createObject(t, t, 1)
t.setTo(t1)
t1.untake()

t.take()
t.take()
t.take()
t.untake()
t.untake()
t1 = createObject(t, t, 2)
t.setTo(t1)
t1.untake()

t.take()
t.take()
t.take()
t.untake()
t.untake()
t1 = createObject(t, t, 3)
t.setTo(t1)
t1.untake()

t.take()
t.take()
t.take()
t.untake()
t.untake()
t1 = createObject(t, t, 4)
t.setTo(t1)
t1.untake()
print(t)
t.o.decrOwn()

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
    print(cls, cls.code)
