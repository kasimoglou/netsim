import json
import base64
import logging
import os
import sys
from datavis.json2plots import ViewsPlotsDecoder
from datavis.model2plots import create_simulation_results
from datavis.datavis_logger import DatavisProcess
from models.validation import fatal, inform
from datavis.results2json import JsonOutput

from simgen.datastore import context


logger = logging.getLogger('datavis')


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
            context.datastore.update_root_object(data)

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
            context.datastore.update_root_object(data)

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


def generate_output():
    """
    Main function for output generation.

    This function postprocesses the results of a Castalia simulation and uploads the
    generated plots and files to the Project Repository.
    """


    simulation_id = context.datastore.sim_id

    # output_list will hold all info/error messages of GenerateResultsProcess
    output_list = []
    pf = DatavisProcess.new_factory(output_list)
    results_json = None
    with pf(name='GenerateResultsProcess') as proc:
        
        plot_models = transform_nsd_plots()

        if proc.success:
            #
            # Get the results of the simulation
            #
            results_json = create_simulation_results(simulation_id, plot_models)
            results_json_string = json.dumps(results_json, default=lambda o: o.__dict__, indent=2)

            with open("results.json", "w") as f:
                print(results_json_string, file=f)

    if not proc.success:
        for msg in output_list:
            print(msg['level'],msg['message'], file=sys.stderr)
        raise RuntimeError("The output generation stage has failed")


    if results_json is None:
        jo = JsonOutput("simulation_results", simulation_id)
        results_json = jo.get_json()

    for i in output_list:
        print(i["message"])

    simoutput_handler = SimOutputHandler()
    simoutput_handler.finish_job(results_json)



def validate_output():
    """
    Validate the NSD and create the plot models
    """
    context.validate = True
    transform_nsd_plots()
    inform("NSD data analysis validated.")


def transform_nsd_plots():

    filename = "nsd.json"

    vpd = ViewsPlotsDecoder()
    with open(filename, "r") as f:
        json_str = f.read()

    nsd = json.loads(json_str)

    if "views" not in nsd:
        inform("There are no output definitions in the NSD")
        nsd["views"] = []

    #
    #  DerivedTable, PlotModel creation from nsd
    #
    #  if this fails we abort result generation
    #  this is what happens when we validate the nsd
    #
    derived_tables, plot_models = vpd.decode(nsd["views"])

    return plot_models 
