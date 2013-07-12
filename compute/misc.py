from sage.all import QQ

coeff_x, coeff_y, alpha_s, alpha_t = QQ['x,y,s,t'].gens()
DEBUG = True # debug prints

def prod(items):
	'''Returns the product of a bunch of items'''
	result = 1
	for i in items: result *= i
	return result
