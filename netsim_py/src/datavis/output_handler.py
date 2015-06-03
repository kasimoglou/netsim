import json
import base64
import logging
import os
from datavis.json2plots import ViewsPlotsDecoder
from datavis.model2plots import create_simulation_results
from models.validation import Process, fatal

from simgen.datastore import context


class SimOutputHandler:
    def __init__(self):
        self.status = 'FINISHED'

    def finish_job(self, results_json):
        try:
            if (self.status == 'ABORTED'):
                self.create_null_SIMOUTPUT()
            else:
                self.create_SIMOUTPUT(results_json)
        except:
            logging.exception("Cannot create json file")



        #
        # Creates the SIMOUTPUT json file in case where ABORTED
        #

    def create_null_SIMOUTPUT(self):
        data = context.datastore.get_root_object()
        try:
            data["simulation_status"] = self.status
            data["node_plot_results"] = []
            data["node_parameter_results"] = []
            data["network_plot_results"] = []
            data["network_parameter_results"] = []
            data["node_2_node_results"] = []
            data["type"] = "simoutput"

            # Write json data to SIMOUTPUTx
            logging.info("Data = %s", data)
            context.datastore.put_root_object(data)

        except:
            logging.exception("Wrong json content")


    #
    # Creates the SIMOUTPUT json file and stores
    #all the simulation results
    #
    def create_SIMOUTPUT(self, results_json):

        data = context.datastore.get_root_object()

        try:
            data["simulation_status"] = self.status
            data["node_plot_results"] = results_json['node_plot_results']
            data["node_parameter_results"] = results_json['node_parameter_results']
            data["network_plot_results"] = results_json['network_plot_results']
            data["network_parameter_results"] = results_json['network_parameter_results']
            data["node_2_node_results"] = results_json['node_2_node_results']
            data["type"] = "simoutput"

            data['_attachments'] = {}
            self.add_attachments_inline(data, 'network_plot_results')

            #Write json data to SIMOUTPUTx
            logging.info("Data = %s", data)
            context.datastore.put_root_object(data)

        except:
            logging.exception("Wrong json content")

    def add_attachments_inline(self, obj, field):
        for fdecl in obj[field]:
            fname = fdecl['file_id']
            with open(fname, 'rb') as f:
                fdata = f.read()
            obj['_attachments'][fname] = {
                'content_type': 'image/png',
                'data': base64.b64encode(fdata).decode('ascii')
            }

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

    simulation_id = context.datastore.sim_id
    filename = "nsd.json"
    castalia_data = "simout.txt"

    #
    # Get the results of the simulation
    #
    with Process():
        vpd = ViewsPlotsDecoder()
        with open(filename, "r") as f:
            json_str = f.read()

        logging.root.debug("The nsd is:\n%s", json.dumps(json.loads(json_str), indent=4))

        nsd = json.loads(json_str)
        if "views" not in nsd:
            nsd["views"] = []
        try:
            derived_tables, plot_models = vpd.decode(nsd["views"])
        except Exception as ex:
            fatal("{}\nAborting results generation".format(ex))

        results_json = create_simulation_results(simulation_id, plot_models, castalia_data)
        results_json_string = json.dumps(results_json, default=lambda o: o.__dict__, indent=2)
        logging.root.debug("Results in json are:\n%s", json.dumps(json.loads(results_json_string), indent=2))
        with open(fileloc + "/results.json", "w") as f:
            print(results_json_string, file=f)

        simoutput_handler = SimOutputHandler()
        simoutput_handler.finish_job(results_json)
        
