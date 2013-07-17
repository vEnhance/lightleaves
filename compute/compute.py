from bs_graph import Component, Vertex, Universe
from alg import action_s, action_t
from alg import prod
from alg import DEBUG
import copy

def getDirection(u,v):
	if u > v: u,v = v,u
	return 1 if v == u.right_up else 0

	



def evaluateForm(leaf1, leaf2):
	letters = leaf1.letters
	n = len(letters)
	if leaf1.top != leaf2.top: return "INCOMPATIBLE"

	# Initialize vertices and edges 
	vertices = [Vertex(i, letters[i]) for i in range(n)]
	for e in leaf1.edges:
		a,b = sorted(e[1:3])
		vertices[a].destinations[1] = vertices[b] # left up
		vertices[b].destinations[0] = vertices[a] # right up
	for e in leaf2.edges:
		a,b = sorted(e[1:3])
		vertices[a].destinations[2] = vertices[b] # right down
		vertices[b].destinations[3] = vertices[a] # left down
	# 
	# Find out where the top is divided
	dividers_top = [vertices[x[1]] for x in leaf1.nodes_open]
	dividers_bottom = [vertices[x[1]] for x in leaf2.nodes_open]
	assert len(dividers_top) == len(dividers_bottom), "..."
	# Determines connected components and cycles 
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

	# 
	# Check if already 0 mod lower terms, otherwise get the components corresponding to each 
	dividers = []
	for i in range(len(dividers_top)):
		if dividers_top[i].component != dividers_bottom[i].component: return 0
		else:
			c = dividers_top[i].component
			dividers.append(c)
			c.is_divider = True
			c.divider_tip = dividers_top[i]
			c.divider_base = dividers_bottom[i]
			c.setDividerPath()
			if DEBUG: print "Assign", c, c.divider_tip, c.divider_base

	# 
	# Feed things into pockets 
	universe = Universe() # temp pointer
	for c in components:
		universe.feed(c)
	# 
	# Mark certain pockets/components as attached to an identity line 
	for c in components:
		for p in c.outer_pockets[:-1]:
			p.attached = True
		if c.is_divider and len(c.outer_pockets) > 0:
			c.outer_pockets[-1].attached = True
	# 
	# Split into regions by dividers and evaluate each region 
	final_result = 1
	top_level_components = copy.copy(universe.contents) # elements here are removed as evaluated
	if DEBUG: print "TOPLEVEL", top_level_components
	if DEBUG: print "DIVIDERS", dividers
	for d in sorted(dividers, key = lambda d: -d.divider_tip.name):
		# Evaluate polynomials to the right of the divider
		for c in top_level_components:
			if d.hasOnRight(c):
				final_result *= c.evaluate()
				top_level_components.remove(c)
		# Apply barbell forcing rules modulo lower terms
		if final_result == 0:
			return 0 # gg
		elif final_result == 1:
			pass 
		else:
			if d.color == 's': final_result = action_s(final_result)
			else: final_result = action_t(final_result)
	else:
		final_result *= prod([c.evaluate() for c in top_level_components]) # the rest of the components, left of all dividers
	# 
	return final_result

# vim: fdm=marker
