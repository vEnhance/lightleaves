from sage.all import QQ, PolynomialRing

Z, (x,y) = PolynomialRing(QQ, 2, 'xy').objgens()
R, (s,t) = PolynomialRing(Z, 2, 'st').objgens()
DEBUG = False # debug prints

def prod(items):
	'''Returns the product of a bunch of items'''
	result = 1
	for i in items: result *= i
	return result


def div_s(f): return sum([s**(exp[0]-1) * t**(exp[1]) * coeff for exp, coeff in f.dict().iteritems()])
def div_t(f): return sum([s**(exp[0]) * t**(exp[1]-1) * coeff for exp, coeff in f.dict().iteritems()])

def action_s(f): return f.subs(s=-s, t=t + x*s)
def action_t(f): return f.subs(t=-t, s=s + y*t)
def demazure_s(f): return div_s(f-action_s(f))
def demazure_t(f): return div_t(f-action_t(f))


# Pre-computed: first several quantum numbers
QUANTUM_X = [0,1,x]
QUANTUM_Y = [0,1,y]

def computeQuantum(N):
	'''Increase the range of quantum numbers to N'''
	for n in range(len(QUANTUM_X), N):
		QUANTUM_X.append(x*QUANTUM_Y[n-1] - QUANTUM_X[n-2])
		QUANTUM_Y.append(y*QUANTUM_X[n-1] - QUANTUM_Y[n-2])
computeQuantum(15) # initial things

def getQuantum(P):
	if P == 1: return ''
	if P == -1: return '-'
	d = P.degree() # maximum degree
	for i in xrange(d+2,1,-1):
		if i % 2 == 1:
			quo, rem = P.quo_rem(QUANTUM_X[i])
			if rem == 0: return getQuantum(quo) + '[%d]' %i
		else:
			quo, rem = P.quo_rem(QUANTUM_Y[i])
			if rem == 0: return getQuantum(quo) + '[%d]_y' %i
			quo, rem = P.quo_rem(QUANTUM_X[i])
			if rem == 0: return getQuantum(quo) + '[%d]_x' %i
	return "(" + str(P) + ")"

def quantize(f):
	if type(f) == type(0): return f
	if f == 0: return f
	if f == "INCOMPATIBLE": return f
	terms = [getQuantum(f.monomial_coefficient(m)) + (str(m) if m != 1 else '') for m in f.monomials()]
	return '+'.join(terms)


# For exporting
coeff_x = x
coeff_y = y
alpha_s = s
alpha_t = t
