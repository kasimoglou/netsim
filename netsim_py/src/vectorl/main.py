
from vectorl.model import ModelFactory
from vectorl.runtime import Runner
from vectorl.utils import FileModelFactory

from os.path import dirname, basename, join
import argparse



def main():

    parser = argparse.ArgumentParser(description='''
    This is a compiler and executor for vectorl. It takes as input a uri to the
    desired module and then compiles and executes (unless -c is given) the model.
    ''')

    parser.add_argument("src",  help="The uri of the vectorl source.")
    
    parser.add_argument("--path", '-p', type=str, help="""Provide a list of directories separated by
        : to search in vectorl files.""", default="")

    parser.add_argument("--compile", '-c',
                        action="store_true",
                        help="""Only compile the given file, do not run it.""")

    #parser.add_argument("--repo", '-r',
    #                    type=str,
    #                    help="""The url of the project repository to use.""")
    args = parser.parse_args()

    fmf = FileModelFactory()
    for d in args.path.split(':'):
        fmf.add(d)

    fname = args.src
    dname, bname = dirname(fname), basename(fname)
    if dname:
        fmf.add(dname)
    else:
        fmf.add(".")
    if bname.endswith('.vl'):
        bname = bname[:-3]

    model = fmf.get_model(bname)
    if not args.compile:
        Runner(fmf).start()

    return fmf

if __name__=='__main__':
    factory = main()

