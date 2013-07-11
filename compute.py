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
	def __repr__(self):
		return "v_%d" %(self.name)
	#clockwise starting from right_up
	neighbors = [None None None None] # clockwise from left up
	#right_up = None
	#right_down = None
	#left_up = None
	#left_down = None
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
		# get all edges
		edge = []
		for v in self.members:
			for j in range(0,4):
				if(v.neighbors[j] != None):
					edge.append([v,j])

	
		#iterate through vertices
		v = self.members[0]
		pocketList = [v]
		dir = 0
		while v.neighbors[dir] !=None: # this is not the right condition
			edge.remove([v,dir])
			v = v.neighbors[dir]
			if v in pocketList: # we found a cycle
				#TODO: if its NOT the exterior cycle
				self.pockets.append(Pocket(pocketList, self))
				# restart
				pocketList = []
			else
				pocketList.append(v)
			switch(dir){
				case 1:
					dir = 3
					break;
				case 3:
					dir = 1
					break;
			}

			if v.neighbors[dir] == None:
				dir = (dir - 1)%4
			if v.neighbors[dir] == None:
				dir = (dir - 1)%4
			if v.neighbors[dir] == None:
				# there is nowhere to go, pick a random edge
				v = edge[0][0]

		
		
		assert len(self.left_break) == len(self.right_break), str(self.left_break)+" "+str(self.right_break)
		self.left_break.sort()
		self.right_break.sort()
		for i in range(len(self.left_break)):
			self.pockets.append(Pocket(
				start = self.left_break[i],
				end = self.right_break[i],
				parent = self))
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
			if v.right_up > target: num_covers_from_heaven += 1
		
		# do work
		res = (0 if self.divider_tip > self.divider_base else 1) + num_covers_from_heaven # even = left, odd = right
		return (res % 2 == 1)

class Pocket:
	attached = False # attached to some other thing
	def __init__(self, vertices, parent):
		self.vertices = []
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
		'''Returns True if the component is contained in this pocket'''
		if component == self: return False # reflexive check
		target = component.members[0] # a point on the component we want to test
		if len(self.vertices) == 2: # edge case: trivial pocket
			return target > min(self.vertices) and target < max(self.vertices)
		else:
			num_covers_from_heaven = 0 # number of arcs shielding it from the sky
			num_covers_from_hell = 0 # number of arcs shielding it from below
			for i in range(len(self.vertices)):
				if i != len(self.vertices) - 1: a,b = sorted([self.vertices[i], self.vertices[i+1]])
				else: a,b = sorted([self.vertices[-1], self.vertices[0]])
				if a < target and target < b:
					if a.right_up == b: num_covers_from_heaven += 1
					elif a.right_down == b: num_covers_from_hell += 1
					else: assert 0, str(a) + " " + str(b)
			assert num_covers_from_heaven % 2 == num_covers_from_hell % 2, "well then"
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
		vertices[a].right_up = vertices[b]
		vertices[b].left_up = vertices[a]
	for e in leaf2.edges:
		a,b = sorted(e[1:3])
		vertices[a].right_down = vertices[b]
	vertices[b].left_down = vertices[a]
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
			for i in (v.right_up, v.right_down): # i is a vertex
				if i is None: continue
				flood(i,c)
	num_components = 0
	components = []
	# look for each component to flood fill
	for v in vertices:
		if v.component is not None: continue # already added this vertex to some component

		new_component = Component(num_components, v) 
		flood(v, new_component) # flood fill to find components
		new_component.members.sort()

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
	for d in sorted(dividers, key = lambda d: -d.divider_tip):
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
