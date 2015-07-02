
from models.validation import Process

from vectorl.model import ModelFactory
from vectorl.runtime import Runner
from vectorl.utils import FileModelFactory
from vectorl.cppgen import CppGenerator

from os.path import dirname, basename, join
import argparse


factory = None

def main():

    global factory

    parser = argparse.ArgumentParser(description='''
    This is a compiler and executor for vectorl. It takes as input a uri to the
    desired module and then compiles and executes (unless -c is given) the model.
    ''')

    parser.add_argument("src",  help="The uri of the vectorl source.")
    
    parser.add_argument("--path", '-p', type=str, help="""Provide a list of directories separated by
        : to search in vectorl files.""", default="")

    parser.add_argument("--until", "-u", type=float, help="""The simulation time at which 
the simulation will end. The default is 'no limit'""" , default=None)

    parser.add_argument("--steps", "-s", type=int, help="""The maximum number of steps (events) to process.
 The default is 'no limit'""", default=None)

    parser.add_argument("--compile", '-c',
                        action="store_true",
                        help="""Only compile the given file, do not run it.""")

    parser.add_argument("--gen", '-g',
                        action="store_true",
                        help="""Generate C++ code from this model, do not run it.""")

    #parser.add_argument("--repo", '-r',
    #                    type=str,
    #                    help="""The url of the project repository to use.""")
    args = parser.parse_args()

    fmf = FileModelFactory()
    factory = fmf
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

    with Process() as compile:
        model = fmf.get_model(bname)

    if not compile.success:
        return fmf

    if not (args.compile or args.gen):
        runner = Runner(fmf)
        fmf.runner = runner
        runner.start(until=args.until, steps=args.steps)
        if runner.event_queue:
            print("Finished at time=", runner.now,"after", 
                runner.step, "steps, unprocessed events=",len(runner.event_queue))
    elif args.gen:
        gen=CppGenerator(fmf, bname)
        gen.generate()
        print(gen.hh.output_string())
        print(gen.cc.output_string())
        #print(gen.output_hh)
        #print(gen.output_cc)


    return fmf

if __name__=='__main__':
    factory = main()

