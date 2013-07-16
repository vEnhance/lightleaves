from sage.all import QQ, PolynomialRing, FractionField, factor

Z, (x,y) = FractionField(PolynomialRing(QQ, 2, 'xy')).objgens()
R, (s,t) = PolynomialRing(Z, 2, 'st').objgens()
DEBUG = False # debug prints

def prod(items):
	'''Returns the product of a bunch of items'''
	result = 1
	for i in items: result *= i
	return result

def quotient(f,g): 
	res = f.quo_rem(g)
	assert res[1] == 0
	return res[0]

def action_s(f): return f.subs(s=-s, t=t + x*s)
def action_t(f): return f.subs(t=-t, s=s + y*t)
def demazure_s(f): return quotient(f-action_s(f), s)
def demazure_t(f): return quotient(f-action_t(f), t)

# Pre-computed: first several quantum numbers
QUANTUM_X = [0,1,x]
QUANTUM_Y = [0,1,y]

def computeQuantum(N):
	'''Increase the range of quantum numbers to N'''
	for n in range(len(QUANTUM_X), N):
		QUANTUM_X.append(x*QUANTUM_Y[n-1] - QUANTUM_X[n-2])
		QUANTUM_Y.append(y*QUANTUM_X[n-1] - QUANTUM_Y[n-2])
computeQuantum(9) # initial things

def getQuantum(q):
	if q == 1: return ''
	if q == -1: return '-'
	if q in QUANTUM_X:
		i = QUANTUM_X.index(q)
		if i % 2 == 1: return "[%d]" %i
		return "[%d]_x" % QUANTUM_X.index(q)
	if q in QUANTUM_Y:
		return "[%d]_y" % QUANTUM_Y.index(q)

	q = -q # lol so bad
	if q in QUANTUM_X:
		i = QUANTUM_X.index(q)
		if i % 2 == 1: return "-[%d]" %i
		return "-[%d]_x" % QUANTUM_X.index(q)
	if q in QUANTUM_Y:
		return "-[%d]_y" % QUANTUM_Y.index(q)

	q = -q
	return "(%s)" %q


def quantize(f):
	if type(f) == type(0): return f
	terms = [getQuantum(f.monomial_coefficient(m)) + (str(m) if m != 1 else '') for m in f.monomials()]
	return '+'.join(terms)


# For exporting
coeff_x = x
coeff_y = y
alpha_s = s
alpha_t = t
