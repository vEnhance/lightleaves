from lightleaf import LightLeaf
from compute import evaluateForm

import itertools
import sys

L = 8


letters = sys.stdin.readline().strip()
n = len(letters)

def prettyEval(leaf1, leaf2):
	'''Return the output of evaluateForm in TeX with s -> \\alpha_s, etc.'''
	res = str(evaluateForm(leaf1, leaf2))
	if str(res) == '0': return ''
	the_expr = str(res).replace('s', r'\alpha_s').replace('t', r'\alpha_t').replace("*","") 
	the_expr.replace("+", "+\\nobreak ").replace("-", "-\\nobreak ")
	return "$" + the_expr + "$"

def chunks(seq, l):
	n = len(seq)
	i = 0
	while i < n:
		yield seq[i:i+l]
		i += l


# Compute all bit sequences
all_maps_by_top = {} # sorted by top_panel
for bit_seq in itertools.product("01", repeat=n):
	bits = ''.join(bit_seq)
	m = LightLeaf(bits, letters)
	all_maps_by_top[m.top] = all_maps_by_top.get(m.top, []) + [m]

print r"""\documentclass[11pt,landscape]{scrartcl}
\usepackage[left=2cm,right=2cm,top=2cm,bottom=3cm]{geometry}
\usepackage{amsmath,amsthm,amssymb}
\begin{document}
\title{""" + letters + r"""}
\author{RSI 2013}
\date{\today}
\maketitle
"""

for top, maps in all_maps_by_top.iteritems():
	print r"\section{" + letters + r" $\to$ " + (top if top != "" else r"$\varnothing$") + "}" # create a section for this top
	for columns in chunks(maps, L):
		l = len(columns)
		width = 2.7
		print r"\begin{tabular}" + "{r|" + ("|p{%.2fcm}" %(width)) * l + "}" # start the table
		print top, '&',
		print ' & '.join([m.bits for m in columns]),
		print r"\\ \hline"
		for a in maps:
			print a
			for b in columns:
				try:
					print "&", prettyEval(a,b),
				except AssertionError:
					assert False, str( [a,b] )
			print r"\\"

		print r"\end{tabular}"
		print

print r"\end{document}"
