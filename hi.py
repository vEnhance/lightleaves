import sys
import os

for line in sys.stdin:
	letters = line.strip()
	os.system("echo \"%s\" | sage -python matrices.py > out.tex" % letters)
	os.system("latexmk out")
	os.system("cp out.pdf reversed/%s.pdf" %letters)
	os.system("cp out.tex reversed/%s.tex" %letters)

