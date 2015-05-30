
import pytest, io
from models.validation import Process
from vectorl.model import ModelFactory, Model, Scope
from vectorl.tests.modelfactory import *


@pytest.fixture
def tmf():
        return TestModelFactory()

#
# Test that all these programs do not compile
#
@pytest.mark.parametrize('source',[

	# initialization of variables and defs
	"var int a = 0; const int x = a;",
	"var int a=0; var int b=a;",

	# bad assignments
	"import sys; var int a = 0; def int b = 1; on sys.Init b:=a;",
	"import sys; var int a = 0; def int b = 1; on sys.Init b:=a;",
	"import sys; var bool a = true; on sys.Init a := [1,2];",
	"import sys; var bool a = true; on sys.Init a[2] := [1,2];",
	"import sys; var bool a = [true,false]; on sys.Init a[0:1] := [1,2];",

	# if statement
	"import sys; var bool a = true; on sys.Init if([1,2]) a:=false;",
	"import sys; var bool a = true; on sys.Init if(2) a:=false;",
	"import sys; var bool a = true; on sys.Init if(2) a:=false; else a:=!a;",

	# event declaration
	"event foo(int i, int i);",
	"event foo(int i, int j); event foo();",
	"import sys; event sys.foo();",
	"event foo()",

	# function declaration
	"int x=1;",
	"def int x() { 1 };",
	"def int x(int a) { x(a+1) } ",
	"def int y=x; \n def int x(int a) { y(a+1) } ",
	"def int f(int x) { x[0:3] } def int y=f([1,2]);",

	# variable declaration
	"var int a=1; var int a=2;",
	"import sys; var int a=1; on sys.Init { def int a=1; a:=2; }",
	"import sys; var int a=1; def int x=a; on sys.Init { x:=a,a; }",


	# bad index range
	"def int b = [1,2][1,2,3];",
	"def int b = [1,2][1:3];",
	"def int b = [1,2][1:2:-1];",
	"def int b = [1,2][1:-1:2];",
	"def int b = [1,2][-1:2:-1];",
	"def int b = [1,2][1:-1:-1];",
	"def int b = [1,2][2::4];",

	# emit statement
	"import sys; event foo(); on sys.Init emit foo(1) after 1;",
	"import sys; event foo(int a); on sys.Init emit foo() after 1;",
	"import sys; event foo(); var time a=[1]; on sys.Init emit foo() after a;",
	"import sys; event foo(time x); var time a=[1]; on sys.Init emit foo(a) after 1;",

	# done
	"empty"
	])
def test_error(tmf, source):
	tmf.add_source('bad', source)
	with Process() as p:
		print("source:",source)
		model = tmf.get_model('bad')

	assert not p.success

