# netsim

In order to run Netsim project:

1. Install `python3`
2. Create a postgresql database named `dpcm`
3. Install `omnet++` and just unzip somewhere `castalia` package. 
4. Place `netsim_py/src/sample.dpcm_netsim` to your home directory, renaming it to `.dpcm_netsim`. Change `execdir` and `netsim_py` to the corresponding paths of your system.
6. Execute `setup_castalia.py` placed in `netsim_py/src`.  
7. Execute `python3 sim_runner.py --ll INFO` (install any missing packages). `sim_runner.py` is placed in `netsim_py/src` directory.

Visit `localhost:18880/admin` to have access to our tools.
