#import sys
from lightleaf import LightLeaf

class Vertex:
	def __init__(self, i):
		self.name = i
	def __repr__(self):
		return "v_%d" %(self.name)
	up = None
	down = None
	component = None
	def __eq__(self, other):
		if other is None: return False
		return self.name == other.name
	def __lt__(self, other):
		return self.name < other.name
	def __gt__(self, other):
		return self.name > other.name

def get_direction(u,v):
	if u > v: u,v = v,u
	return 1 if v == u.up else 0

class Component:
	def __init__(self, number, start):
		self.name = number
		self.breakpoints = [start]
		self.pockets = []
	def __repr__(self):
		return "c_%s = %s" %(self.name, self.breakpoints)
	def addBreakpoint(self, vertex):
		self.breakpoints.append(vertex)
		self.breakpoints.sort()
	def makePockets(self):
		if len(self.breakpoints) == 1: return # is a barbell
		for i in range(len(self.breakpoints)-1):
			self.pockets.append(Pocket(
				start = self.breakpoints[i],
				end = self.breakpoints[i+1],
				parent = self)
				)

class Pocket:
	def __init__(self, start, end, parent):
		self.start = start
		self.end = end
		self.parent = parent # should be a component
		self.contents = []
	def __repr__(self):
		return "(%s, %s) in c_%s" %(self.start, self.end, self.parent.name)
	def feed(self, c):
		for component in self.contents:
			for pocket in component.pockets:
				if pocket.contains(c):
					pocket.feed(c)
					return
		self.contents.append(c)

	def contains(self, component):
		# Returns True if component is inside said thing
		# Sanity checks
		if component == self: return False # reflexive check
		if len(self.parent.breakpoints) == 1: return False # barbells never contain anything

		start = self.start
		end = self.end
		target = component.breakpoints[0] # a point on the component we want to test

		if target.name <= start.name or target.name >= end.name: return False # another sanity check

		checkpoints = [v for v in vertices[start.name:end.name+1] if v.component == self.parent] # points of the loop
		if len(checkpoints) == 2: return True # loops are always good if the earlier sanity check returned OK

		switchpoints = [start] # points where direction changes
		for i in range(1, len(checkpoints)-1):
			v = checkpoints[i]
			if get_direction(checkpoints[i-1], v) != get_direction(v, checkpoints[i+1]):
				switchpoints.append(v)
		switchpoints.append(end)
		assert len(switchpoints) % 2 == 0
		# Find the pair of switchpoints a,b such that a < target < b and look at parity
		for i in range(0, len(switchpoints)-1): 
			if switchpoints[i] > target:
				return (i % 2 == 1)


# Get input {{{1
f = open("data.in", "r")
letters = f.readline().strip()
n = len(letters)
bit1 = f.readline().strip()
bit2 = f.readline().strip()
assert len(bit1) == n, "bad length"
assert len(bit2) == n, "bad length"

# Get lightleaf data
leaf1 = LightLeaf(bit1, letters)
leaf2 = LightLeaf(bit2, letters)

if leaf1.top != leaf2.top:
	print "INCOMPATIBLE"
	exit()

# Find out where the top is divided
# If I'm right, shouldn't matter whether leaf1 or leaf2 is used
dividers = [x[1] for x in leaf1.nodes_open]
assert sum([x[1] for x in leaf2.nodes_open]) == sum(dividers), "you suck at life"
# }}}1
# Initialize vertices and edges {{{1
vertices = [Vertex(i) for i in range(n)]
for e in leaf1.edges:
	a,b = sorted(e[1:3])
	vertices[a].up = vertices[b]
for e in leaf2.edges:
	a,b = sorted(e[1:3])
	vertices[a].down = vertices[b]
# }}}1
# Determines connected components and cycles {{{1

# Connected components
def infiltrate(v, c):
	# Colors everything connected to v with color c
	# returns True if a cycle is detected and False otherwise
	#if v is None: return
	assert type(v) != type(0), "fix your types"
	if v.component == c: # Cycle detected, remember and quit
		c.addBreakpoint(v)
		return
	assert v.component is None, "Houston, we have a problem."
	v.component = c
	for i in (v.up, v.down): # i is a vertex
		if i is None: continue
		infiltrate(i, c)
		
num_components = 0
components = []
for v in vertices:
	if v.component is not None: continue # already done
	new_component = Component(num_components, v)
	components.append(new_component)
	infiltrate(v, new_component) # flood fill
	new_component.makePockets() # construct the pockets for this component
	num_components += 1


# print [v.component_num for v in vertices]
# print cycle_endpoints
# }}}1
# Feed things into pockets {{{1
class Diagram(Pocket):
	def __init__(self):
		self.contents = []
	def __repr__(self):
		return str(self.contents)
	def contains(self, component):
		return True
universe = Diagram() # temp pointer
for c in components:
	universe.feed(c)
del universe
# }}}1

if __name__ == "__main__":
	print components[0].pockets[0].contains(components[1])
	for comp in components:
		for p in comp.pockets:
			print p, p.contents
# vim: fdm=marker
