import sys
sys.path.append(".")
from lightleaf import LightLeaf
from compute import evaluateForm

if __name__ == "__main__":
	letters = sys.stdin.readline().strip()
	bit1 = sys.stdin.readline().strip() 
	bit2 = sys.stdin.readline().strip()
	n = len(letters)
	assert len(bit1) == n, "bad length"
	assert len(bit2) == n, "bad length"

	# Get lightleaf data
	leaf1 = LightLeaf(bit1, letters)
	leaf2 = LightLeaf(bit2, letters)
	res = evaluateForm(leaf1, leaf2)

	print res
