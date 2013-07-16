from sage.all import QQ, PolynomialRing, FractionField

Z, (coeff_x, coeff_y) = FractionField(PolynomialRing(QQ, 2, 'xy')).objgens()
R, (alpha_s, alpha_t) = PolynomialRing(Z, 2, 'st').objgens()
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

def action_s(f): return f.subs(s=-alpha_s, t=alpha_t + coeff_x*alpha_s)
def action_t(f): return f.subs(t=-alpha_t, s=alpha_s + coeff_y*alpha_t)
def demazure_s(f): return quotient(f-action_s(f), alpha_s)
def demazure_t(f): return quotient(f-action_t(f), alpha_t)

