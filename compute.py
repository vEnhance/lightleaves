#import sys
from lightleaf import LightLeaf

class Vertex:
	def __init__(self, i):
		self.name = i
	def __repr__(self):
		return "%d" %(self.name)
	up = None
	down = None
	component_num = None
	# in_cycle = False

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

# Initialize vertices
vertices = [Vertex(i) for i in range(n)]
# Initialize edges
for e in leaf1.edges:
	a,b = sorted(e[1:3])
	vertices[a].up = b
for e in leaf2.edges:
	a,b = sorted(e[1:3])
	vertices[a].down = b


# Connected components
def infiltrate(v, c):
	# Colors everything connected to v with color c
	# returns True if a cycle is detected and False otherwise
	#if v is None: return
	if v.component_num == c: # Cycle detected, remember and quit
		cycle_endpoints[c].append(v)
		return
	assert v.component_num is None, "Houston, we have a problem."
	v.component_num = c
	for i in (v.up, v.down):
		if i is None: continue
		infiltrate(vertices[i], c)
		
num_components = 0
cycle_endpoints = {}
for v in vertices:
	if v.component_num is not None: continue # already done
	cycle_endpoints[num_components] = [v]
	infiltrate(v, num_components)
	# cycle_endpoints[num_components] = set(cycle_endpoints[num_components])
	num_components += 1

print [v.component_num for v in vertices]
print cycle_endpoints
