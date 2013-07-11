from lightleaf import LightLeaf
from sage.all import QQ, factor, expand
import copy
import sys

coeff_x, coeff_y, alpha_s, alpha_t = QQ['x,y,s,t'].gens()

def prod(items):
	'''Returns the product of a bunch of items'''
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
		'''Creates in pockets a list of all planar faces of this graph'''
		leafless_vertices = copy.copy(self.members)
		# kill all vertices with degree 1.  RECURSIVELY!!!!
		new_degrees = {} # v.name -> temp degree
		for v in self.members: new_degrees[v.name] = v.degree
		# adjust degrees for trivial pockets
		for v in leafless_vertices:
			u = v.destinations[1]
			if u == v.destinations[2] and u is not None:
				self.pockets.append(Pocket([v,u],self)) # add the trivial pocket
				new_degrees[u.name] -= 1
				new_degrees[v.name] -= 1
		# kill a bunch of extraneous vertices
		to_kill = [v for v in leafless_vertices if new_degrees[v.name] <= 1]
		while len(to_kill) > 0:
			for v in to_kill:
				leafless_vertices.remove(v)
				for u in v.neighbors:
					new_degrees[u.name] -= 1
			to_kill = [v for v in leafless_vertices if new_degrees[v.name] <= 1]
		 
		# Generate directed edges
		edges = []
		for v in leafless_vertices:
			u1 = v.destinations[1] # right up
			u2 = v.destinations[2] # right down
			if u1 == u2 and u1 is not None: # it's a trivial pocket
				edges.append((v,1))
				edges.append((v,0))
			else:
				if u1 is not None:
					edges.append((v,1))
					edges.append((u1,0))
				if u2 is not None:
					edges.append((v,2))
					edges.append((u2,3))

		if len(leafless_vertices) == 0:
			# is a barbell now
			return
	
		# walk always to the right
		v_0 = leafless_vertices[0]
		v = v_0
		pocket_list = [v_0]
		direction = 1 # ok since deg v >= 2 and nothing to left, so both 1 and 2 exist
		is_first_face = True # flag

		while len(edges) > 0:
			edges.remove( (v,direction) )
			# Walk along this directed edge
			v = v.destinations[direction]

			if v in pocket_list: 
				# we found a face!!!
				if (not v_0 in pocket_list) or is_first_face:
					self.pockets.append(Pocket(pocket_list, self)) # create the corresponding pocket
				if is_first_face: is_first_face = False
				if len(edges) == 0:
					break # we're done, we're done, we're done!
				v, direction = edges[0] # respawn
				pocket_list = [v] 
			else:
				pocket_list.append(v)
				# change direction
				direction = (0,3,2,1)[direction] # this is the new "ideal" direction
				num_tries = 0
				while not (v, direction) in edges:
					direction = (direction - 1) % 4
					num_tries += 1
					assert num_tries <= 4, v

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
		if self.divider_tip == self.divider_base: return target > self.divider_tip # if the divider is just a straight line, yay

		# count the number of arcs covering
		num_covers_from_heaven = 0
		for v in self.members:
			assert v != target, "What have you done?"
			if v > target: break # all future arcs too far right
			if v.right_up is None: continue
			if v.right_up > target: num_covers_from_heaven += 1
		
		# do work
		res = (0 if self.divider_tip > self.divider_base else 1) + num_covers_from_heaven # even = left, odd = right
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

def evaluateForm(leaf1, leaf2):
	letters = leaf1.letters
	n = len(letters)
	if leaf1.top != leaf2.top: return "INCOMPATIBLE"

	# Initialize vertices and edges {{{1
	vertices = [Vertex(i, letters[i]) for i in range(n)]
	for e in leaf1.edges:
		a,b = sorted(e[1:3])
		vertices[a].destinations[1] = vertices[b] # left up
		vertices[b].destinations[0] = vertices[a] # right up
	for e in leaf2.edges:
		a,b = sorted(e[1:3])
		vertices[a].destinations[2] = vertices[b] # right down
		vertices[b].destinations[3] = vertices[a] # left down
	# }}}1
	# Find out where the top is divided
	dividers_top = [vertices[x[1]] for x in leaf1.nodes_open]
	dividers_bottom = [vertices[x[1]] for x in leaf2.nodes_open]
	assert len(dividers_top) == len(dividers_bottom), "..."
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
			for i in v.neighbors: # i is a vertex
				flood(i,c)
	num_components = 0
	components = []
	# look for each component to flood fill
	for v in vertices:
		if v.component is not None: continue # already added this vertex to some component
		new_component = Component(num_components, v) 
		flood(v, new_component) # flood fill to find components
		new_component.members.sort() # sort the new vertices
		components.append(new_component) # add to master list of components
		new_component.makePockets() # construct the pockets for this component
		num_components += 1

	# }}}1
	# Check if already 0 mod lower terms, otherwise get the components corresponding to each {{{1
	dividers = []
	for i in range(len(dividers_top)):
		if dividers_top[i].component != dividers_bottom[i].component: return 0
		else:
			c = dividers_top[i].component
			dividers.append(c)
			c.is_divider = True
			c.divider_tip = dividers_top[i]
			c.divider_base = dividers_bottom[i]

	# }}}
	# Feed things into pockets {{{1
	universe = Universe() # temp pointer
	for c in components:
		universe.feed(c)
	# }}}1
	# Mark certain pockets/components as attached to an identity line {{{1
	for c in components:
		for p in c.pockets[:-1]:
			p.attached = True
		if c.is_divider and len(c.pockets) > 0:
			c.pockets[-1].attached = True
	# }}}
	# Split into regions by dividers and evaluate each region {{{1
	final_result = 1
	top_level_components = copy.copy(universe.contents) # elements here are removed as evaluated
	for d in sorted(dividers, key = lambda d: -d.divider_tip.name):
		# Evaluate polynomials to the right of the divider
		for c in top_level_components:
			if d.has_on_right(c):
				final_result *= c.evaluate()
				top_level_components.remove(c)
		# Apply barbell forcing rules modulo lower terms
		if final_result == 0:
			return 0 # gg
		elif final_result == 1:
			pass 
		else:
			if d.color == 's': final_result = final_result.subs(s = -alpha_s, t = alpha_t + coeff_x * alpha_s)
			else: final_result = final_result.subs(t = -alpha_t, s = alpha_s + coeff_y * alpha_t)
	else:
		final_result *= prod([c.evaluate() for c in top_level_components]) # the rest of the components, left of all dividers
	# }}}
	return final_result, components

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
	res, components = evaluateForm(leaf1, leaf2)

	print res
# vim: fdm=marker
