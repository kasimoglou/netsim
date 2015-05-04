'''
Utilities for code generation.

Created on Sep 23, 2014

@author: vsam
'''


import os.path, logging, sys
from subprocess import check_call
from multiprocessing import Process, Queue
from runner.config import configure, cfg


#
#   WHOLE FILE ACCESS
#


def put_file(path, data, fmode = 'w'):
    '''Write a string to a file.
    
    Write to file <path> the contents of binary string <data>.
    The previous contents of the file, if it exists, are overwritten.
    
    Return the number of bytes written.
    '''
    assert fmode in ('w', 'x', 'a')
    with open(path, fmode+'b') as f:
        f.write(str(data).encode('utf8'))

def put_new_file(path, data):
    '''Write a string to a file.
    
    Write to file <path> the contents of binary string <data>.
    If the file already exists, raise an error. 
    Return the number of bytes written.
    '''
    return put_file(path, data, fmode='x')


def append_to_file(path, data):
    '''Append a string to a file.
    
    Append the contents of binary string <data> to file <path>.
    
    Return the number of bytes written.
    '''
    return put_file(path, data, 'a')



def get_file(path):
    '''Return the contents of a file as a binary string.'''
    with open(path, 'rt', encoding='utf8') as f:
        return f.read()


#
#  PROCESS EXECUTION
#


def execute_command(fileloc, args, stdstr_suffix, redirect=True):
    '''
    Execute a unix program with redirection.
    
    fileloc - the current directory cwd at the start of execution
    args -  a string list containing the executed program and its arguments
    stdstr_suffix - a suffix for the files containing the redirected  output
    redirect - a boolean indicating whether stdout and stderr should be redirected.
    
    Example:
    execute_command("/", ['/bin/ls'], 'ls', True)
    
    will execute /bin/ls at the / directory and create two files: /stdout.ls and /stderr.ls
    (if the process has permission to write these files to the root
    directory) or fail with an exception.
    '''
    
    # jump to fileloc
    sout, serr = None, None
    try:
        if redirect:
            sout = open(os.path.join(fileloc, "stdout."+stdstr_suffix), 'w')
            serr = open(os.path.join(fileloc, "stderr."+stdstr_suffix), 'w')
        
        check_call(args, cwd=fileloc, stdout=sout, stderr=serr)
    finally:
        if redirect:
            sout.close()
            serr.close()




# Module-private util for execute_function
def _procwrapper(queue, cfgsection, fileloc, func, stdstr_suffix, redirect, args, kwargs):
    try:
        curdir = os.getcwd()
        os.chdir(fileloc)
        if redirect:
            sout = open(os.path.join(fileloc, "stdout.%s.txt" % stdstr_suffix),'w')
            serr = open(os.path.join(fileloc, "stderr.%s.txt" % stdstr_suffix),'w')
            origs = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = sout, serr

        try:
            # configuration file
            configure(cfgsection)

            retval = (True, func(*args, **kwargs))
        except Exception as e:
            logging.info("In execute_function (toplevel)", exc_info=1)
            retval = (False, e)

        queue.put(retval)
    finally:
        if redirect:
            sys.stdout, sys.stderr = origs
            sout.close()
            serr.close()
        os.chdir(curdir)



def execute_function(fileloc, func, stdstr_suffix, redirect, *args, **kwargs):
    """
    Execute a python function in a new process, with redirection.

    fileloc - the current directory at the start of execution, also passed as argument to the
            called function.
    func -  a python function to call
    stdstr_suffix - a suffix for the files containing the redirected  output
    redirect - a boolean indicating whether stdout and stderr should be redirected.
    
    Example:
    execute_function("/", foo, 'ls', True, 1 , k=3)
    
    will execute call foo(1, k=3) in a new process (created by the 'multiprocessing' module) 
    in the / directory and create two files: /stdout.ls and /stderr.ls
    (if the process has permission to write these files to the root
    directory) or fail with an exception.

    """
    queue = Queue()
    proc = Process(target=_procwrapper,  
        args=(queue, cfg.section, fileloc, func, stdstr_suffix, redirect, args, kwargs) )
    proc.start()
    ok, value = queue.get()
    proc.join()
    if ok:
        return value
    else:
        raise value



#
#  TEMPLATES
#

def docstring_template(func):
    """A function decorator that returns a template created from the function docstring.
    
    Example:
    
    @docstring_template
    def hi(name):
      '''Hello {{name}}'''
      return locals()
      
    hi('vsam')  -> "Hello vsam"
    
    """
    import functools
    from bottle import template
    
    @functools.wraps(func)
    def inline_template_func(*args, **kwargs):
        tparams = func(*args, **kwargs)
        return template(func.__doc__, tparams)
    return inline_template_func

