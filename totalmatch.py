from lightleaf import LightLeaf
import itertools
import os
import sys
letters = sys.stdin.readline().strip()
n = len(letters)

maps = {}

for bit_seq in itertools.product("01", repeat=n):
	bits = ''.join(bit_seq)
	m = LightLeaf(bits, letters)
	maps[m.top] = maps.get(m.top, []) + [m]

def printAll():
	os.system("mkdir res_%s" %letters)
	for top in maps.keys():
		os.system("mkdir res_%s/top_%s" %(letters, top))
		for diag in maps[top]:
			filename = "res_%s/top_%s/%s.asy" %(letters, top, diag)
			pdfname = filename[:-4]
			out = open(filename, 'w')
			print >>out, diag.printPreamble()
			print >>out, diag.drawLines()
			print >>out, diag.drawLabels()
			out.close()
			os.system("asy -f pdf -o %s %s" %(pdfname, filename))
			os.system("rm %s" %filename)
		for pair in itertools.combinations_with_replacement(maps[top], 2):
			diag1 = pair[0]
			diag2 = pair[1]
			filename = "res_%s/top_%s/prod_%s_%s.asy" %(letters, top, diag1, diag2)
			pdfname = filename[:-4]
			out = open(filename, 'w')
			print >>out, diag1.printPreamble()
			print >>out, "picture one;"
			print >>out, diag1.drawLines("one")
			print >>out, "picture two;"
			print >>out, diag2.drawLines("two")
			print >>out, "add(one); add(reflect((0,0),(1,0))*two);"
			print >>out, "draw((-1,0)--(%d,0));" %n
			out.close()
			os.system("asy -f pdf -o %s %s" %(pdfname, filename))
			os.system("rm %s" %filename)

if __name__=="__main__":
	print maps
