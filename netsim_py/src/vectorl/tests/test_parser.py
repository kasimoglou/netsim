
import pytest, io
from vectorl.model import ModelFactory, Model, Scope
from vectorl.tests.modelfactory import *

from vectorl.runtime import Runner



MF1 = [
    ('foo', ""),
    ('bar', "import foo;")
]

MF2 = MF1+[
    ('baz', """
    import bar;
    from bar import foo;
    import foo1 = foo;
    import foo2 = foo;
        """)
]

def test_parse_imports():
    tmf = TestModelFactory(sources=MF1)

    bar = tmf.get_model('bar')

    assert isinstance(bar, Model)
    assert len(bar.imports)==1
    foo = tmf.get_model('foo')

    assert foo in bar.imports

def test_parse_imports2():
    tmf = TestModelFactory(sources=MF2)
    baz = tmf.get_model('baz')
    assert 'foo' in tmf.symtab
    assert 'bar' in tmf.symtab
    assert tmf.symtab['foo'] is baz.symtab['foo1']
    assert tmf.symtab['foo'] is baz.symtab['foo2']

BADMF1 = MF2 + [
('bad', """
    import foo;
    import foo;
    """)
]

BADMF2 = MF2 + [
('bad', """
    import foo1 = foo;
    import foo1 = foo;
    """)
]


BADMF3 = MF2 + [
('bad1',"""
    import foo1 = foo;
    import foo1 = foo;
    """),
('bad', """
    import foo1 = foo;
    import bad1;
    """)
]



@pytest.fixture(params=[BADMF1, BADMF2, BADMF3,
    [('bad', "@lexerror")],
    [('bad', ";")],
    [('bad', "garba g e  inthetext")],
    [('bad', "import foo")]
    ])
def import_errors(request):
    return request.param


def test_parse_import_error_throws(import_errors):
    with pytest.raises(Exception):
        tmf = TestModelFactory(import_errors, val)
        model = tmf.get_model('bad')


@pytest.fixture(params=[
    ('evt', "event foo();"),
    ('evt', "event foo(int a);"),
    ('evt', "event foo(real x);"),
    ('evt', "event foo(bool p);"),
    ('evt', "event foo(bool a, bool b, real x );")
    ])
def event_decl(request):
    return request.param

def test_event_decl(event_decl):
    tmf = TestModelFactory(sources=[event_decl])
    model = tmf.get_model('evt')
    assert model

BIGMF = [
    ('sim', 
"""
var time now=0;
"""),

    ('cars', 
"""
import sim;

def time now = sim.now;
//from sim import now;

//// First car will come in the parking at 9, the second at 9.15 etc
const time carInTime = [9, 9.15, 9.30, 10] ; 

//// The first car that came at 9 will leave at 10, the second at 9:30, etc
const time carOutTime = [10, 9.30, 10.15, 10.30];

var int arrival = 0;

//// First car will go to slot 1 and second car to slot 2. 
//// The third car arrives when second car has left so it will go to lot 2, etc
const int carSpot = [0,1,1,0];  


//  
//// This is what we want. The sensor measurements (taken or not) at each
//// time
var bool spotTaken = [false, false]; 

//// i is index    

event carIn(int i);
event carOut(int i);

on carIn { // line 22
    def int pos = carSpot[i];
    const real PI = 3.14;
    spotTaken[pos] := !spotTaken[pos];

    // schedule departure
    emit carOut(arrival) after carOutTime[arrival]-now;

    // schedule arrival of next car 
    arrival := arrival + 1;
    if(arrival < shapeof(carInTime)[0])
        emit carIn(arrival) after carInTime[arrival]-now;
}    

on carOut {    
    def int pos = carSpot[i];
    spotTaken[pos] := !spotTaken[pos];
}



on Init {
    // arrival of first car
    emit carIn(arrival) after carInTime[arrival] - now;
}

const real noise = [1.4, 1.9];

def real noisy_measurement(int k) {
    def int spots = shapeof(spotTaken)[0];
    def real varnoise = spots*noise;

    varnoise[carSpot[k]]
}

event measurement(int i, real val);

on carOut {
    if( i < shapeof(carSpot)[0] )
        emit measurement(i, noisy_measurement(i)) after 1.0;
    else
        print("We are done",10,20,"bye");
}


""")
]

def test_big_parse():
    tmf = TestModelFactory(sources=BIGMF)
    model = tmf.get_model('cars')
    assert model

    Runner(tmf).start()


