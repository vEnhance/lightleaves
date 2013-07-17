from facebook import findFaces
from alg import alpha_s, alpha_t, demazure_s, demazure_t
from alg import prod
from alg import DEBUG

def divides(f, g):
	'''Returns f | g'''
	return f.quo_rem(g)[1] == 0

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
		self.outer_pockets = []
		self.all_pockets = []
	def __repr__(self):
		return "c_%s = %s" %(self.name, self.members)
	@property
	def color(self):
		return self.members[0].color
	def makePockets(self):
		self.all_pockets = [Pocket(packet, self) for packet in findFaces(self.members)]
		if DEBUG: "***", "Built pockets", self.all_pockets
		for p in self.all_pockets:
			# Check to see if ALL arcs are part of another bounded face
			for arc in p.arcs:
				flip_arc = (arc[1], arc[0])
				for p2 in self.all_pockets:
					if flip_arc in p2.arcs and p != p2:
						# This one is, so darn, keep looking for arcs
						break
				else:
					# This one is an exit
					self.outer_pockets.append(p)
					break
			else:
				# OK, this pocket is completely surrounded
				# Take the most recent p2 and append it, I guess
				p2.embedded_pockets.append(p)
				p.attached = True
			

	def evaluate(self):
		if len(self.all_pockets) == 0: # is a barbell
			if self.is_divider: return 1
			else: return alpha_s if self.color == 's' else alpha_t
		else:
			return prod([pocket.evaluate() for pocket in self.outer_pockets])

	def setDividerPath(self):
		'''Returns a path from divider_tip to divider_base as a bunch of vertices'''
		path = []
		def search(v):
			path.append(v)
			if v == self.divider_tip: return 1
			for n in v.neighbors:
				if n in path: continue
				if search(n) == 1: return 1
			assert path[-1] == v
			path.pop()
			return 0
		search(self.divider_base)
		assert len(path) > 0
		self.divider_path = path

	def hasOnRight(self, component):
		'''Returns True if the component is strictly to the right of this divider.  Throws an AssertionError if self.is_divider is False'''
		assert self.is_divider, str(self) + " isn't a divider"

		# Sanity checks / edge cases
		if component == self: return False # reflexive check
		target = component.members[0] # arbitrary point on target we wish to check
		if self.divider_tip == self.divider_base:
			if DEBUG: print "IMMED", self, component, "AS RESULT", int(target > self.divider_tip)
			return target > self.divider_tip # if the divider is just a straight line, yay

		# count the number of arcs covering
		divider_path = self.divider_path
		num_covers_from_heaven = 0
		for i in xrange(len(divider_path)-1):
			a,b = sorted(divider_path[i:i+2])
			if a.right_up == b and a < target and b > target:
				num_covers_from_heaven += 1

		# do work
		res = (0 if self.divider_tip > target else 1) + num_covers_from_heaven # even = left, odd = right
		if DEBUG: print "RESOLVE", self, component, "AS RESULT", res
		return (res % 2 == 1)

class Pocket:
	attached = False # attached to some other thing
	def __init__(self, vertices, parent):
		self.vertices = vertices
		self.parent = parent # should be a component
		self.contents = []
		self.embedded_pockets = []
		self.arcs = [(self.vertices[i], self.vertices[i+1]) for i in range(len(self.vertices)-1)]
		self.arcs.append((self.vertices[-1], self.vertices[0]))
		
	def __repr__(self):
		return "%s in c_%s" %(self.vertices, self.parent.name)
	@property
	def color(self): return self.parent.color
	@property
	def left(self): return min(self.vertices)
	@property
	def right(self): return max(self.vertices)

	def feed(self, c):
		for component in self.contents:
			for pocket in component.all_pockets:
				if pocket.contains(c):
					pocket.feed(c)
					return
		for pocket in self.embedded_pockets:
			if pocket.contains(c):
				pocket.feed(c)
				return
		self.contents.append(c)
	def evaluate(self):
		if len(self.contents) == 0: return 0
		f = prod([thing.evaluate() for thing in self.contents])
		if f == 0: return 0
		# Evaluate the contents
		res = demazure_s(f) if self.color == 's' else demazure_t(f)
		if self.attached is False:
			res *= alpha_s if self.color == 's' else alpha_t
		# Multiply by any embedded pockets
		return res * prod([pocket.evaluate() for pocket in self.embedded_pockets])

	def contains(self, component):
		'''Returns True if the component is contained in this pocket'''
		if component == self: return False # reflexive check
		target = component.members[0] # a point on the component we want to test
		if len(self.vertices) == 2: # edge case: trivial pocket
			return target > min(self.vertices) and target < max(self.vertices)
		else:
			num_covers_from_heaven = 0 # number of arcs shielding it from the sky
			num_covers_from_hell = 0 # number of arcs shielding it from below
			for arc in self.arcs:
				a,b = sorted(arc) # a -> b is an arc from left to right
				if a < target and target < b:
					if a.right_up == b: num_covers_from_heaven += 1
					elif a.right_down == b: num_covers_from_hell += 1
					else: assert 0, str(a) + " " + str(b)
			assert num_covers_from_heaven % 2 == num_covers_from_hell % 2, "well then"
		return (num_covers_from_heaven % 2 == 1)

#	def breakPolynomial(self, monomial):
#		'''Returns the result of breaking a monomial out of a loop with some color'''
#
#		# If barbell of same color
#		if divides(same, monomial):
#			if self.attached:
#				return 2 * monomial/same - same * self.breakPolynomial(monomial / same)
#			else:
#				return 2 * monomial - same * self.breakPolynomial(monomial / same)
#		elif divides(diff, monomial):
#			if self.attached:
#				return (-coeff) * monomial / diff + (diff + coeff * same) * self.breakPolynomial(monomial / diff)
#			else:
#				return (-coeff) * monomial / diff * same + (diff + coeff * same) * self.breakPolynomial(monomial / diff)
#		return 0

class Universe(Pocket):
	def __init__(self):
		self.contents = []
		self.embedded_pockets = []
	def __repr__(self):
		return str(self.contents)
	def contains(self, component):
		return True
	def evaluate(self):
		return prod([thing.evaluate() for thing in self.contents])

