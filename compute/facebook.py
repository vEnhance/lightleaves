import copy
from misc import DEBUG

def getEdges(vertices):
	'''Generate the directed eges'''
	edges = []
	for v in vertices:
		u1 = v.destinations[1] # right up
		u2 = v.destinations[2] # right down
		if u1 == u2 and u1 in vertices: # it's a trivial pocket
			edges.append((v,1))
			edges.append((u1,0))
		else:
			if u1 in vertices:
				edges.append((v,1))
				edges.append((u1,0))
			if u2 in vertices:
				edges.append((v,2))
				edges.append((u2,3))
	return edges

def findFaces(vertices):
	# kill all vertices with degree 1.  RECURSIVELY!!!!
	new_degrees = {} # v.name -> temp degree
	for v in vertices: new_degrees[v.name] = v.degree
	# adjust degrees for trivial pockets
	for v in vertices:
		u = v.destinations[1]
		if u == v.destinations[2] and u is not None:
			yield [v,u]
			new_degrees[u.name] -= 1
			new_degrees[v.name] -= 1
	# kill a bunch of extraneous vertices
	leafless_vertices = copy.copy(vertices) # to modify
	to_kill = [v for v in leafless_vertices if new_degrees[v.name] <= 1]
	while len(to_kill) > 0:
		for v in to_kill:
			leafless_vertices.remove(v)
			for u in v.neighbors:
				new_degrees[u.name] -= 1
		to_kill = [v for v in leafless_vertices if new_degrees[v.name] <= 1]
	# Generate directed edges
	edges = getEdges(leafless_vertices)

	if DEBUG is True:
		print "CALLING makePockets"
		print "Initial edges", edges

	if len(leafless_vertices) == 0:
		# is a barbell now
		return

	# walk always to the right
	v_0 = leafless_vertices[0]
	v = v_0
	pocket_list = [v_0]
	direction = 1 # ok since deg v >= 2 and nothing to left, so both 1 and 2 exist
	# in fact, to prove it...
	assert (v,1) in edges, "nvm"
	assert (v,2) in edges, "nvm"
	dir_memory = {}

	while len(edges) > 0:
		edges.remove( (v,direction) )

		# Walk along this directed edge
		if DEBUG: print "Taking", v, "->",
		v = v.destinations[direction]
		if DEBUG: print v

		dir_memory[v.name] = direction # Remember which direction we came from
		if DEBUG: print dir_memory

		if v in pocket_list: 
			# we found a face!!!
			i = pocket_list.index(v)
			cycle_list = pocket_list[i:]
			if DEBUG: print "Completed cycle", cycle_list

			# this is a non-outer face iff the leftmost vertex was entered from below; i.e. entered from a 3 edge
			leftmost_vertex = min(pocket_list)
			leftmost_entry_dir = dir_memory[leftmost_vertex.name]
			assert leftmost_entry_dir in (0,3), (leftmost_vertex, dir_memory)

			if leftmost_entry_dir == 3: yield cycle_list
			if len(edges) == 0: break # we're done, we're done, we're done!

			v, direction = edges[0] # respawn
			pocket_list = pocket_list[:i] + [v]


		else:
			pocket_list.append(v)
			# change direction
			direction = (0,3,2,1)[direction] # this is the new "ideal" direction
			num_tries = 0
			while not (v, direction) in edges:
				direction = (direction - 1) % 4
				num_tries += 1
				assert num_tries <= 4, "well gg"

