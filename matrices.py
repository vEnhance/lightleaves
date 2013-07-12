from lightleaf import LightLeaf
from compute import evaluateForm

import itertools
import sys

L = 6


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

print r"""\documentclass[11pt]{scrartcl}
\usepackage[left=1.414cm,right=1.414cm,top=2cm,bottom=3cm]{geometry}
\usepackage{amsmath,amsthm,amssymb}
\usepackage{longtable}
\usepackage{fancyhdr}
\pagestyle{fancy}
\lhead{RSI 2013}
\rhead{\nouppercase\leftmark}
\begin{document}
\title{Complete Product Matrix for """ + letters + r"""}
\author{Evan Chen \\ under the direction of \\ Francisco Unda, Ben Elias, and Tanya Khovanova}
\date{RSI 2013}
\maketitle
"""

for top, maps in sorted(all_maps_by_top.iteritems(), key = lambda pair: len(pair[1])):
	print r"\section{" + letters + r" $\to$ " + (top if top != "" else r"$\varnothing$") + "}" # create a section for this top
	print r"\subsection*{There are a total of " + str(len(maps)) + r" map(s).}"
	for columns in chunks(maps, L):
		l = len(columns)
		width = 2.24
		print r"\begin{longtable}" + "{|l|" + ("|p{%.2fcm}" %(width)) * l + "|}" # start the table

		print "\hline"
		print top, '&',
		print ' & '.join([m.bits for m in columns]),
		print r"\\ \hline"
		print r"\endfirsthead"

		print top, '&',
		print ' & '.join([m.bits for m in columns]),
		print r"\\ \hline"
		print r"\endhead"

		print r"\endfoot"

		print r"\hline"
		print r"\endlastfoot"

		for a in maps:
			print a
			for b in columns:
				try:
					print "&", prettyEval(a,b),
				except AssertionError:
					assert False, str( [a,b] )
			print r"\\"

		print r"\end{longtable}"
		print

print r"\end{document}"
