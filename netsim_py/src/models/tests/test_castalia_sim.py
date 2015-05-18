
import pytest
import io
from models.castalia_sim import *
from models.mf import validate_classes


def test_validate_model():
	
	with io.StringIO() as outfile:
		val = validate_classes(MODEL, outfile=outfile, detail=20)
		if not val:
			print(outfile.getvalue())
	assert val
