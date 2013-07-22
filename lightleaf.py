import sys


class LightLeaf():
	def __init__(self, bits, letters):
		assert len(bits) == len(letters), "bad length"
		n = len(bits)
		self.bits = bits
		self.letters = letters

		edges = [] # triples (color, a, b) gives a -> b
		stubs = [] # pairs (color, i)
		nodes_open = [] # pairs (color, i)

		for i in range(n):
			curr_color = letters[i]
			if bits[i] == '0':
				if len(nodes_open) == 0:
					stubs.append((curr_color, i))
				elif nodes_open[-1][0] != curr_color:
					stubs.append((curr_color, i))
				else:
					edges.append((curr_color, nodes_open[-1][1], i))
					nodes_open.pop()
					nodes_open.append((curr_color, i))
			elif bits[i] == '1':
				if len(nodes_open) == 0:
					nodes_open.append((curr_color, i))
				elif nodes_open[-1][0] != curr_color:
					nodes_open.append((curr_color, i))
				else:
					edges.append((curr_color, nodes_open[-1][1], i))
					nodes_open.pop()
		self.edges = edges
		self.stubs = stubs
		self.nodes_open = nodes_open
	@property
	def top(self):
		return ''.join([self.letters[x[1]] for x in self.nodes_open])
	def __repr__(self):
		return self.bits

	def printPreamble(self):
		out = ""
		out += "size(10cm);\n"
		out += "real h = 0.7;\n"
		out += "pen s = blue, t = red + dashed + 0.6;\n"
		out += "pen dot_s = blue, dot_t = red;\n"
		out += "int n = %d;\n" %len(self.bits)
		return out
	def drawLines(self, pic = "currentpicture"):
		out = ""
		if len(self.edges) == 0: max_height = 2
		else: max_height = max(2, max([e[2]-e[1] for e in self.edges]))
		for e in self.edges:
			pen = e[0] #pen to use
			start = e[1] #start
			end = e[2] #end
			diff = end-start
			out += "draw(%(pic)s, (%(start)d,0)--(%(start)d,h/2)..((%(start)d+%(end)d)/2.0,h*%(diff)d)..(%(end)d,h/2)--(%(end)d,0), %(pen)s);\n" \
				% {'pic' : pic, 'start': start, 'end': end, 'diff': diff, 'pen': pen}
		for x in self.stubs:
			out += "draw(%s, (%d,0)--(%d,h), %s);\n" %(pic, x[1],x[1],x[0])
			out += "dot(%s, (%d,h), dot_%s);\n" %(pic, x[1],x[0])
		for x in self.nodes_open:
			out += "draw(%s,(%d,0)--(%d,%d*h), %s);\n" %(pic, x[1], x[1], max_height + 1, x[0])
		starting_points = [e[1] for e in self.edges] + [x[1] for x in self.nodes_open]
		ending_points = [e[2] for e in self.edges] 
		for x in starting_points:
			if x in ending_points:
				out += "dot(%s, (%d, h/2), dot_%s);\n" %(pic, x, self.letters[x])
		return out
	def drawLabels(self, pic = "currentpicture"):
		out = ""
		for i in xrange(len(self.bits)):
			out += "label(%s, \"%s\", (%d,-1.5h), dir(90));\n" %(pic, self.bits[i], i)
			out += "label(%s, \"%s\", (%d,-0.8*h), dir(90));\n" %(pic, self.letters[i], i)
		return out
	def drawAll(self, pic = "currentpicture"):
		out = ""
		out += self.printPreamble()
		out += self.drawLines(pic)
		out += self.drawLabels(pic)
		return out



#if __name__ == "__main__":
#	letters = sys.stdin.readline().strip() # e.g. tstst
#	bit1 = sys.stdin.readline().strip() # e.g. 10111
#	bit2 = sys.stdin.readline().strip() # e.g. 10111
#	diag1 = LightLeaf(bit1, letters)
#	diag2 = LightLeaf(bit2, letters)
#	print diag1.printPreamble()
#	print "picture one;"
#	print diag1.drawLines("one")
#	print "picture two;"
#	print diag2.drawLines("two")
#	print "add(one); add(reflect((0,0),(1,0))*two);"
#	print "draw((-1,0)--(%d,0));" %len(bit1)

if __name__ == "__main__":
	letters = sys.stdin.readline().strip()
	bits = sys.stdin.readline().strip()
	print LightLeaf(bits, letters).drawAll()
