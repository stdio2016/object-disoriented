import argparse
import sys

args = argparse.ArgumentParser()
args.add_argument('file', help='Object Disoriented program')
args.add_argument('--objcnt', action='store_true')
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
        # tail call optimization
        if code[-1] == 'f':
            code[-1] = 'fr'
        if len(code) > 3 and code[-3:] == ['f','*','z']:
            code[-3:] = ['frz']
        self.a = a
        self.b = b
        self.name = name
    def __repr__(self):
        return "<class %s>" % self.name

objcnt = 0
stepcnt = 0
class Ref:
    def __init__(self, o):
        self.o = o
    def setTo(self, p):
        # c command
        self.o = p.o.copy()
    def __repr__(self):
        if self.tmp: return '&'+str(self.o)
        return str(self.o)

class Obj:
    def __init__(self, a, b, f):
        global objcnt
        objcnt += 1
        self.a = Ref(a)
        self.b = Ref(b)
        self.f = f
    def __del__(self):
        #print(self.f.name, self.vis(), self.own())
        pass
    def isZero(self):
        return False
    def copy(self):
        return Obj(self.a.o.copy(), self.b.o.copy(), self.f)
    def __repr__(self):
        return "%s{a=%s b=%s}"%(
            self.f.name, self.a, self.b
        )

class Zero(Obj):
    def __init__(self):
        global objcnt
        objcnt += 1
        self.a = 0
        self.b = 1
    def isZero(self):
        return True
    def __repr__(self):
        return "z"
    def copy(self):
        return Zero()
    def flip(self):
        self.a, self.b = self.b, self.a

def createObject(a, b, klass):
    out = Ref(Obj(a.o.copy(), b.o.copy(), klass))
    return out

bitbuffer = [0, 0]
def outputBit(bit):
    bitbuffer[0] = bitbuffer[0]*2 + bit
    bitbuffer[1] += 1
    if bitbuffer[1] == 8:
        bitbuffer[1] = 0
        sys.stdout.write(chr(bitbuffer[0]))
        sys.stdout.flush()
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

def runFunc(s, p, indent=0):
    self = s.o
    returnZ = False
    if self.isZero():
        self.flip()
        return s
    #print('-'*indent+'enter', self.f.name)
    t = Ref(Zero())
    stack = []
    i = 0
    code = self.f.code
    global stepcnt
    while i < len(code):
        op = code[i]
        i += 1
        stepcnt += 1
        if op == 'f':
            p0 = stack.pop()
            s0 = stack.pop()
            stack.append(runFunc(s0, p0, indent+1))
        elif op == 'z':
            stack.append(Ref(Zero()))
        elif op == 'a':
            stack.append(self.a)
        elif op == 'b':
            stack.append(self.b)
        elif op == 'p':
            stack.append(p)
        elif op == 's':
            stack.append(s)
        elif op == 't':
            stack.append(t)
        elif op == 'c':
            ddest = stack.pop()
            ssrc = stack.pop()
            ddest.setTo(ssrc)
        elif op == '*':
            stack.pop()
        elif op == '?':
            print(hash(stack[-1]), stack[-1])
        elif op == 'o':
            what = stack.pop()
            onetest = Ref(Zero())
            onetest0 = onetest.o
            runFunc(what, onetest)
            outputBit(onetest0.a)
        elif op == 'i':
            if inputBit() == 0:
                stack.append(Ref(Zero()))
            else:
                stack.append(createObject(Ref(Zero()), Ref(Zero()), klasses['.one']))
        elif op == 'fr' or op == 'frz':
            if op == 'frz':
                returnZ = True
            # release object

            # call object
            p = stack.pop()
            s = stack.pop()
            self = s.o
            if self.isZero():
                self.flip()
                return Ref(Zero()) if returnZ else s
            #print('-'*indent+'goto', self.f.name)
            t = Ref(Zero())
            stack = []
            i = 0
            code = self.f.code
        elif isinstance(op, Klass):
            b = stack.pop()
            a = stack.pop()
            stack.append(createObject(a, b, op))
        else:
            raise NotImplementedError(op)
    # release object
    
    #print('-'*indent+'leave', self.f.name)
    return Ref(Zero()) if returnZ else stack[0]

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
main0 = Ref(Obj(Zero(), Zero(), main0_class))
runFunc(main0, Ref(Zero()))
if args.objcnt:
    print("obj %d" % objcnt)
    print("step %d" % stepcnt)
