'''
Created on Oct 24, 2014

@author: vsam
'''
from contextlib import contextmanager
from sys import exc_info
from traceback import extract_tb, format_exception_only
from os.path import basename


######################
# Inline validation
######################


# A stack of contexts (may need this to be thread-local)
ctxstack = []

class Context:
    def __init__(self):
        self.success = True


@contextmanager
def checking():
    cc = Context()
    ctxstack.append(cc)
    try:
        yield 


class CheckFailed(Exception):
    def __init__(self, message, reraise=False):
        self.message = message

def fail(msg, *args, **kwargs):
    message = msg.format(*args, **kwargs)
    reraise = 'reraise' in kwargs and kwargs['reraise']
    raise CheckFailed(message, reraise)





#
#  Model validation
#
    
class Validation:
    """This class is used to log a model validation.
    
    In model validation, there is code that traverses the objects of the
    model and checks the validity of the data. While this is done by
    traditional functions or classes, there is need to keep a detailed account
    of the process, in order to maximize the information returned to the
    user.
    
    It is used as a context manager, and provides methods to
    output a trace of the validation to a file object.
    
    The context manager policy is to ignore all exceptions (but
    record them internally) and continue with the validation.
    
    
    Examples:
    with Validation() as V:
    
        # basic check
        V( x==1 , "check x")
        ...
        if x.failure(): V.fail("An error was detected on {0}",x)
    
        with V:
            # here we may throw, start a with block
            ...
            
        with V.section("My new section"):
            ... check stuff in a section, with indented output
            
            with V.section("My nested section"):
                ...    
    
    """
    
    INDENT_SIZE=4  # number of spaces per indent

    # detail levels
    SUCCESS=0
    INFO=10
    FAIL=20
    SECTION=30
    EXCEPTION=40
    # reserved
    QUIET=100
    
    class Abort(Exception):
        pass
    class MaxFailures(Exception):
        pass
    
    def __init__(self, outfile=None, detail=0, max_failures = 1000):
        # counters
        self.failures = 0                   # number of failures
        self.max_failures = max_failures    # max number of failures to tolerate
        self.enter = 0                      # number of calls to __enter__
        self.section_failures = []

        # output control
        self.detail = detail                # the level of detail to record
        self.level = 0                      # current indentation level
        self.outfile = outfile              # the output file
        self.exc_output_limit = 1           # number of lines per exception
    
        if self.outfile is None:
            self.detail = self.QUIET      
    
    def failure(self):
        self.failures += 1
        if self.section_failures:
            self.section_failures[-1] += 1
        if self.failures>=self.max_failures:
            raise Validation.MaxFailures
        
    def output(self, header, msg, *args, **kwargs):
        if self.outfile is None: return
        out = msg.format(*args, **kwargs)
        # split into lines
        lines = out.split('\n')
        for line in lines:
            if not line: continue
            print(" "*(self.INDENT_SIZE*self.level),
                  sep='', end='', file=self.outfile, flush=True)
            print(header, line,  
                    file=self.outfile, flush=True)
        
    def fail(self, msg, *args, **kwargs):
        self.failure()
        if msg and self.detail <= self.FAIL: 
            self.output("FAIL:", msg, *args, **kwargs)

    def exception(self, etype, evalue, etb):
        self.failure()
        if self.outfile and self.detail <= self.EXCEPTION:
            #for line in format_exception(type, value, tb, self.exc_output_limit):
            #    self.output("EXCEPTION:", line, end='')
            for frame in extract_tb(etb):
                fname, fline, func, _ = frame
                fbase = basename(fname)
                self.output("EXCEPTION:", "{0}({1}): {2}", fbase, fline, func)
            for line in format_exception_only(etype, evalue):
                self.output("EXCEPTION:", line)
    
    def success(self, msg, *args, **kwargs):
        if msg and self.detail <= self.SUCCESS: 
            self.output("SUCCESS:", msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if msg and self.detail <= self.INFO: 
            self.output("INFO:", msg, *args, **kwargs)

    def __enter__(self):
        self.enter += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Propagate Abort or MaxFailures immediately.
        # Other exceptions are swallowed

        self.enter -= 1
        if exc_type is AssertionError:
            return False
        
        if exc_type is None:
            return True

        if exc_type is Validation.Abort or self.failures>=self.max_failures:
            if self.failures==0 and self.enter==0: self.failures+=1
            return self.enter==0  # re-raise exception except if at the top-level

        try:
            if exc_type is not Validation.MaxFailures:
                self.exception(exc_type, exc_val, exc_tb)
        except Validation.MaxFailures:
            return self.enter==0 # newly raised MaxFailures
        else:
            return True # swallow other 


        
    def __call__(self, check, label=None, *args, **kwargs):
        if check:
            self.success(label, *args, **kwargs)
        else:
            self.fail(label, *args, **kwargs)
        
    @contextmanager
    def section(self, msg, *args, **kwargs):
        """Only to be called by a context manager, this starts a new section in the
        validation.
        """
        if msg and self.detail <= self.SECTION:
            self.output("SECTION:", msg, *args, **kwargs)
        self.level += 1
        self.section_failures.append(0)
        try:
            yield self
        except (AssertionError,Validation.MaxFailures,Validation.Abort):
            raise
        except Exception:
            exc_type, exc_value, exc_tb = exc_info()
            self.exception(exc_type, exc_value, exc_tb)
        finally:
            if msg and self.detail <= self.SECTION and self.section_failures[-1]>0:
                self.output("FAIL:", "Section encountered {0} failures.", self.section_failures[-1])
            self.level -= 1
            fcount = self.section_failures.pop()
            # Add subsection failures to parent
            if self.section_failures:
                self.section_failures[-1] += fcount


    def passed(self):
        return self.failures==0
    def passed_section(self):
        if self.section_failures:
            return self.section_failures[-1]==0
        return True


