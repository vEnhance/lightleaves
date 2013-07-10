from lightleaf import LightLeaf
import sys
letters = sys.stdin.readline().strip()
n = len(letters)
bit1 = sys.stdin.readline().strip()
bit2 = sys.stdin.readline().strip()

diag1 = LightLeaf(bit1, letters)
diag2 = LightLeaf(bit2, letters)
out = sys.stdout
print >>out, diag1.printPreamble()
print >>out, "picture one;"
print >>out, diag1.drawLines("one")
print >>out, "picture two;"
print >>out, diag2.drawLines("two")
print >>out, "add(one); add(reflect((0,0),(1,0))*two);"
print >>out, "draw((-1,0)--(%d,0));" %n

from compute import evaluateForm
