'''
Created on Oct 24, 2014

@author: vsam
'''
from models.validation import Validation
import sys



def test_validation():
    
    
    with Validation() as V:
        assert V.failures==0
        V(1==1,"ok")
        assert V.failures==0
        V(1==2,"not ok")
        assert V.failures==1
        with V.section("New section"):
            V(True, "ok")
            assert V.failures==1
            with V.section("New sub section"):
                V(len(1)==1, "throws")
                assert 0, "NOT here!"
            assert V.failures==2
            V(True, "still ok")

    assert V.enter==0
    assert V.level==0
    
    with Validation(max_failures=3) as V:
        assert V.enter==1
        # Check error case
        for i in range(8):
            with V:
                assert V.enter==2
                raise Exception()
            assert V.enter==1
    
    assert V.enter==0
    assert V.failures==V.max_failures
    

def test_validation_failure_count():
    with Validation(outfile=sys.stdout) as V:

        assert V.passed()
        assert V.passed_section()
        
        V.fail(None)
        
        assert V.failures==1
        assert V.section_failures == []
        assert not V.passed()
        assert V.passed_section()
        
        with V.section(None):
            V.fail(None)
            V.fail(None)
            assert V.section_failures[-1]==2
            with V.section(None):
                V.fail(None)
                assert V.section_failures[-1]==1
            assert V.section_failures[-1]==3

