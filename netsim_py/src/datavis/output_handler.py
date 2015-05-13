import json
from pprint import pprint
import random
import subprocess, shlex
import urllib.request
import logging, os
import time
from datavis.json2plots import ViewsPlotsDecoder
from runner.config import cfg

from runner.config import resource_path
from runner.default_json_simoutput import node_plot_results_default, node_parameter_results_default, network_plot_results_default, network_parameter_results_default, node_2_node_results_default
from datavis.tests.test_results2json import executor_final_stage_test as efst
from datavis.model2plots import create_simulation_results

from simgen.datastore import context

class SimOutputHandler:
    def __init__(self):
        self.status = 'FINISHED'

    def finish_job(self):
        try:
            if (self.status == 'ABORTED'):
                self.create_SIMOUTPUT([], [], [], [], [])
            else:
                self.create_SIMOUTPUT(node_plot_results_default, node_parameter_results_default,
                                      network_plot_results_default, network_parameter_results_default,
                                      node_2_node_results_default)
        except:
            logging.exception("Cannot create json file")

    #
    #Creates the SIMOUTPUT json file and stores
    #all the simulation results
    #
    def create_SIMOUTPUT(self, node_plot_results, node_parameter_results, network_plot_results,
                         network_parameter_results, node_2_node_results):

        data = context.datastore.get_root_object()

        try:
            data["simulation_status"] = self.status
            data["node_plot_results"] = node_plot_results
            data["node_parameter_results"] = node_parameter_results
            data["network_plot_results"] = network_plot_results
            data["network_parameter_results"] = network_parameter_results
            data["node_2_node_results"] = node_2_node_results
            data["type"] = "simoutput"

            #Write json data to SIMOUTPUTx
            logging.info("Data = %s", data)
            context.datastore.put_root_object(data)

        except:
            logging.exception("Wrong json content")

    #
    #Update SIMOUTPUT file with couchdb
    #server, which includes rev_id
    #
    def update_simoutput(self, doc):
        jsonfile = open(self.simoutput_file, 'w')
        #data = json.load(doc)
        json.dump(doc, jsonfile)
        jsonfile.close()


def generate_output(fileloc=None):
    logging.getLogger().setLevel('DEBUG')
    try:
        generate(fileloc)
    except Exception as e:
        logging.root.info("Caught exception", exc_info=True)


def generate(fileloc):
    """
    Main function for output generation.

    This function postprocesses the results of a Castalia simulation and uploads the
    generated plots and files to the Project Repository.
    """

    if fileloc is None:
        fileloc = os.getcwd()

    simulation_id = "?"
    filename = "nsd.json"
    castalia_data = "simout.txt"

    #
    # Get the results of the simulation
    #

    vpd = ViewsPlotsDecoder()
    with open(filename, "r") as f:
        json_str = f.read()

    logging.root.debug("The nsd is:\n%s", json.dumps(json.loads(json_str), indent=4))

    derived_tables, plot_models = vpd.decode(json.loads(json_str)["views"])

    results_json = create_simulation_results(simulation_id, plot_models, castalia_data)
    results_json_string = json.dumps(results_json, default=lambda o: o.__dict__, indent=2)
    with open(fileloc + "/results.json", "w") as f:
        print(results_json_string, file=f)

    simoutput_handler = SimOutputHandler()
    simoutput_handler.finish_job()
        
