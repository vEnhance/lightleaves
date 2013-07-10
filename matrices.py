from lightleaf import LightLeaf
from compute import evaluateForm

import itertools
import sys
letters = sys.stdin.readline().strip()
n = len(letters)

def prettyEval(leaf1, leaf2):
	'''Return the output of evaluateForm in TeX with s -> \\alpha_s, etc.'''
	return "$" + str(evaluateForm(leaf1, leaf2)).replace('s', r'\alpha_s').replace('t', r'\alpha_t') + "$"

# Compute all bit sequences
all_maps_by_top = {} # sorted by top_panel
for bit_seq in itertools.product("01", repeat=n):
	bits = ''.join(bit_seq)
	m = LightLeaf(bits, letters)
	all_maps_by_top[m.top] = all_maps_by_top.get(m.top, []) + [m]

print r"""\documentclass[11pt,landscape]{scrartcl}
\usepackage{evan}
\begin{document}
\title{""" + letters + r"""}
\author{RSI 2013}
\date{\today}
\maketitle
"""

for top, maps in all_maps_by_top.iteritems():
	if top != "":
		print r"\section{" + top + "}" # create a section for this top
	else:
		print r"\section{No Top}"
	print r"\begin{tabular}" + "{r|" + "l" * len(maps) + "}" # start the table
	print '-- &',
	print ' & '.join([m.bits for m in maps]),
	print r"\\ \hline"
	for a in maps:
		print a, "&",
		print " & ".join([prettyEval(a,b) for b in maps]),
		print r"\\"
	print r"\end{tabular}"

print r"\end{document}"
