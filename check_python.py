
import sys
import importlib.util

def check_module(modname):
    if not importlib.util.find_spec(modname):
        print("ERROR: The required module '%s' could not be found. Please install it." % modname)
        return False
    return True


def check_python():
    # check versions
    if sys.version_info.major!=3 or sys.version_info.minor<4:
        print("ERROR: The python version found is not suitable for running netsim.")
        print("Please install at least version 3.4 of python3.")
        sys.exit(1)

    # check required modules
    success = True
    for modname in ['psycopg2','pyproj','requests', 'pytest','numpy','cherrypy']:
        succ =  check_module(modname)
        success = success and succ

    if not success:
        sys.exit(1)
    

if __name__=='__main__':
    check_python()
