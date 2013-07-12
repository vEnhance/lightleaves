from sage.all import factor, expand
from facebook import findFaces
from misc import alpha_s, alpha_t, coeff_x, coeff_y
from misc import prod
from misc import DEBUG

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
		self.destinations = [None, None, None, None] # clockwise from left up
		# represents the ''slots'' where neighbors might be
	def __repr__(self):
		return "v_%d" %(self.name)


	@property
	def left_up(self): return self.destinations[0]
	@property
	def right_up(self): return self.destinations[1]
	@property
	def right_down(self): return self.destinations[2]
	@property
	def left_down(self): return self.destinations[3]
	@property
	def degree(self): return len(self.neighbors)
	@property
	def neighbors(self): return [x for x in self.destinations if x is not None]

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
	is_divider = False
	divider_tip = None
	divider_base = None
	
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
		self.pockets = [Pocket(packet, self) for packet in findFaces(self.members)]
		if DEBUG: "***", "Built pockets", self.pockets

	def evaluate(self):
		if len(self.pockets) == 0: # is a barbell
			if self.is_divider: return 1
			else: return alpha_s if self.color == 's' else alpha_t
		else:
			return prod([pocket.evaluate() for pocket in self.pockets])

	def has_on_right(self, component):
		'''Returns True if the component is strictly to the right of this divider.  Throws an AssertionError if self.is_divider is False'''
		assert self.is_divider, str(self) + " isn't a divider"

		# Sanity checks / edge cases
		if component == self: return False # reflexive check
		target = component.members[0] # arbitrary point on target we wish to check
		if self.divider_tip == self.divider_base:
			print "IMMED", self, component, "AS RESULT", int(target > self.divider_tip)
			return target > self.divider_tip # if the divider is just a straight line, yay

		# count the number of arcs covering
		num_covers_from_heaven = 0
		for v in sorted(self.members):
			assert v != target, "What have you done?"
			if v > target: break # all future arcs too far right
			if v.right_up is None: continue
			if v.right_up > target: num_covers_from_heaven += 1
		
		# do work
		res = (0 if self.divider_tip > target else 1) + num_covers_from_heaven # even = left, odd = right
		print "RESOLVE", self, component, "AS RESULT", res
		return (res % 2 == 1)

class Pocket:
	attached = False # attached to some other thing
	def __init__(self, vertices, parent):
		self.vertices = vertices
		self.parent = parent # should be a component
		self.contents = []
	def __repr__(self):
		return "%s in c_%s" %(self.vertices, self.parent.name)
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
		'''Returns True if the component is contained in this pocket'''
		if component == self: return False # reflexive check
		target = component.members[0] # a point on the component we want to test
		if len(self.vertices) == 2: # edge case: trivial pocket
			return target > min(self.vertices) and target < max(self.vertices)
		else:
			num_covers_from_heaven = 0 # number of arcs shielding it from the sky
			num_covers_from_hell = 0 # number of arcs shielding it from below
			for i in range(len(self.vertices)):
				# get the pair of vertices delimited by the arc
				if i != len(self.vertices) - 1:
					a,b = sorted([self.vertices[i], self.vertices[i+1]])
				else:
					a,b = sorted([self.vertices[-1], self.vertices[0]])
				if a < target and target < b:
					if a.right_up == b: num_covers_from_heaven += 1
					elif a.right_down == b: num_covers_from_hell += 1
					else: assert 0, str(a) + " " + str(b)
			assert num_covers_from_heaven % 2 == num_covers_from_hell % 2, "well then"
		return (num_covers_from_heaven % 2 == 1)
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

