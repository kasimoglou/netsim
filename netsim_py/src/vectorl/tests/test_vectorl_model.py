

from models.mf import validate_classes
from vectorl.model import VECTORL_MODEL


def test_validate_vectorl_model():
	import sys
	assert validate_classes(VECTORL_MODEL, outfile=sys.stdout, detail=20)
