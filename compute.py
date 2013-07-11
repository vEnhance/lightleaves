from lightleaf import LightLeaf
from sage.all import QQ, factor, expand
import copy
import sys

coeff_x, coeff_y, alpha_s, alpha_t = QQ['x,y,s,t'].gens()

def prod(items):
	result = 1
	for i in items: result *= i
	return result

def getDirection(u,v):
	if u > v: u,v = v,u
	return 1 if v == u.right_up else 0

def divides(f, g):
	'''Returns f | g'''
	return (f in [ex[0] for ex in list(factor(g))])
	
def getVars(color):
	if color == 's': 
		same = alpha_s
		diff = alpha_t
		coeff = coeff_y
	else: 
		same = alpha_t
		diff = alpha_s
		coeff = coeff_x
	return same, diff, coeff



class Vertex:
	def __init__(self, i, color):
		self.name = i
		self.color = color
	def __repr__(self):
		return "v_%d" %(self.name)
	right_up = None
	right_down = None
	left_up = None
	left_down = None
	component = None
	seen = False # used in reverse floodfill to get left breakpoints
	def __eq__(self, other):
		if other is None: return False
		return self.name == other.name
	def __lt__(self, other): return self.name < other.name
	def __gt__(self, other): return self.name > other.name
	def __le__(self, other): return self.name <= other.name
	def __ge__(self, other): return self.name >= other.name

class Component:
	attached = False
	def __init__(self, number, start):
		self.name = number
		self.left_break = []
		self.right_break = []
		self.members = []
		self.pockets = []
	def __repr__(self):
		return "c_%s = %s" %(self.name, self.members)
	@property
	def color(self):
		return self.members[0].color
	@property
	def num_cycles(self): return len(self.pockets)
	def makePockets(self):
		assert len(self.left_break) == len(self.right_break), str(self.left_break)+" "+str(self.right_break)
		self.left_break.sort()
		self.right_break.sort()
		for i in range(len(self.left_break)):
			self.pockets.append(Pocket(
				start = self.left_break[i],
				end = self.right_break[i],
				parent = self))
	def evaluate(self):
		if len(self.pockets) == 0:
			if self.attached: return 1
			else: return alpha_s if self.color == 's' else alpha_t # barbell
		else:
			return prod([pocket.evaluate() for pocket in self.pockets])



class Pocket:
	attached = False # attached to some other thing
	def __init__(self, start, end, parent):
		self.start = start
		self.end = end
		self.parent = parent # should be a component
		self.contents = []
	def __repr__(self):
		return "(%s, %s) in c_%s" %(self.start, self.end, self.parent.name)
	@property
	def color(self):
		return self.parent.color
	def feed(self, c):
		for component in self.contents:
			for pocket in component.pockets:
				if pocket.contains(c):
					pocket.feed(c)
					return
		self.contents.append(c)
	def evaluate(self):
		if len(self.contents) == 0: return 0
		contents_expr = prod([thing.evaluate() for thing in self.contents])
		if contents_expr == 0: return 0
		contents_poly = expand(factor(contents_expr)) # expand(factor(...)) casts to polynomial
		result = 0
		for coeff, monomial in list(contents_poly):
			result += coeff * self.breakPolynomial(monomial)
		return result
	def contains(self, component):
		# Returns True if component is inside said thing
		# Sanity checks
		if component == self: return False # reflexive check
		# if self.num_cycles == 1: return False # barbells never contain anything
		# TODO ^ why is that there

		start = self.start
		end = self.end
		target = component.members[0] # a point on the component we want to test

		if target.name <= start.name or target.name >= end.name: return False # another sanity check

		checkpoints = [v for v in self.parent.members if start <= v and v <= end] # points of the loop
		if len(checkpoints) == 2: return True # loops are always good if the earlier sanity check returned OK

		switchpoints = [start] # points where direction changes
		for i in range(1, len(checkpoints)-1):
			v = checkpoints[i]
			if getDirection(checkpoints[i-1], v) != getDirection(v, checkpoints[i+1]):
				switchpoints.append(v)
		switchpoints.append(end)
		# assert len(switchpoints) % 2 == 0
		# Find the pair of switchpoints a,b such that a < target < b and look at parity
		for i in range(0, len(switchpoints)-1): 
			if switchpoints[i] > target:
				return (i % 2 == 1)

	def breakPolynomial(self, monomial):
		'''Returns the result of breaking a monomial out of a loop with some color'''
		same, diff, coeff = getVars(self.color)

		# If barbell of same color
		if divides(same, monomial):
			if self.attached: return 2 * monomial/same - same * self.breakPolynomial(monomial / same)
			else: return 2 * monomial - same * self.breakPolynomial(monomial / same)
		elif divides(diff, monomial):
			if self.attached:
				return (-coeff) * monomial / diff + (diff + coeff * same) * self.breakPolynomial(monomial / diff)
			else:
				return (-coeff) * monomial / diff * same + (diff + coeff * same) * self.breakPolynomial(monomial / diff)
		return 0

class Universe(Pocket):
	def __init__(self):
		self.contents = []
	def __repr__(self):
		return str(self.contents)
	def contains(self, component):
		return True
	def evaluate(self):
		return prod([thing.evaluate() for thing in self.contents])

def evaluateForm(leaf1, leaf2):
	letters = leaf1.letters
	n = len(letters)
	if leaf1.top != leaf2.top:
		return "INCOMPATIBLE"
	# Initialize vertices and edges {{{1
	vertices = [Vertex(i, letters[i]) for i in range(n)]
	# Edges are directed a -> b with a < b
	for e in leaf1.edges:
		a,b = sorted(e[1:3])
		vertices[a].right_up = vertices[b]
		vertices[b].left_up = vertices[a]
	for e in leaf2.edges:
		a,b = sorted(e[1:3])
		vertices[a].right_down = vertices[b]
		vertices[b].left_down = vertices[a]
	# Find out where the top is divided
	# If I'm right, shouldn't matter whether leaf1 or leaf2 is used
	dividers = [vertices[x[1]] for x in leaf1.nodes_open]
	# }}}1
	# Determines connected components and cycles {{{1
	def flood(v, c):
		'''Called recursively to flood fill from left'''
		# Colors everything connected to v with color c
		assert type(v) != type(0), "fix your types"
		if v.component == c: return
		else:
			assert v.component is None, "Houston, we have a problem."
			v.component = c
			c.members.append(v)
			for i in (v.right_up, v.right_down): # i is a vertex
				if i is None: continue
				flood(i,c)
	num_components = 0
	components = []
	# look for each component to flood fill
	for v in vertices:
		if v.component is not None: continue # already added this vertex to some component
		# if v.up is None and v.down is None and v in dividers: continue # this is a straight line
		#TODO check ^ doesn't die now
		new_component = Component(num_components, v)
		flood(v, new_component) # flood fill to find components
		new_component.members.sort()
		components.append(new_component) # add to master list of components
		new_component.makePockets() # construct the pockets for this component
		num_components += 1

	# }}}1
	# Feed things into pockets {{{1
	universe = Universe() # temp pointer
	for c in components:
		universe.feed(c)
	# }}}1
	# Mark certain pockets/components as attached to an identity line {{{1
	for c in components:
		for p in c.pockets[:-1]:
			p.attached = True
		if c.members[-1] in dividers:
			if len(c.pockets) > 0: c.pockets[-1].attached = True
			c.attached = True

	# }}}
	# Split into regions by dividers and evaluate each region {{{1
	final_result = 1
	top_level_components = copy.copy(universe.contents) # elements here are removed as evaluated
	for d in reversed(dividers):
		# Evaluate polynomials in the region specified by the divider
		for c in top_level_components:
			if c.members[0] > d:
				final_result *= c.evaluate()
				top_level_components.remove(c)
		# Apply barbell forcing rules modulo lower terms
		if final_result == 0:
			# We're done, return 0
			return 0
		elif final_result == 1:
			pass # nothing needs to be done here
		else:
			if d.color == 's':
				final_result = final_result.subs(s = -alpha_s, t = alpha_t + coeff_x * alpha_s)
			else:
				final_result = final_result.subs(t = -alpha_t, s = alpha_s + coeff_y * alpha_t)
	else:
		final_result *= prod([c.evaluate() for c in top_level_components]) # the rest of the components, left of all dividers
	# }}}
	return final_result

if __name__ == "__main__":
	letters = sys.stdin.readline().strip()
	bit1 = sys.stdin.readline().strip() 
	bit2 = sys.stdin.readline().strip()
	n = len(letters)
	assert len(bit1) == n, "bad length"
	assert len(bit2) == n, "bad length"

	# Get lightleaf data
	leaf1 = LightLeaf(bit1, letters)
	leaf2 = LightLeaf(bit2, letters)
	res = evaluateForm(leaf1, leaf2)

	print res
# vim: fdm=marker
