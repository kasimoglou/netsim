import json
from pprint import pprint
import random
import subprocess, shlex
import urllib.request
import logging, os
import time

from runner.dpcmrepo import PR
from runner.monitor import Manager
from runner.config import resource_path


class SimPreparator:
	def __init__(self):
		#test_sim nsd.json
		self.nsdfile=""
		#test_sim sim.json
		self.simfile=""
		#job's fileloc
		self.simhome=""
		#job id
		self.simjobid=""
		
	#
	#Creates nsd.json and sim.json files
	#necessary for submitting a job object
	#
	def create_runfiles(self, couchdb_response):
		key = random.randint(1, 100000000)
		#create nsd.json
		self.nsdfile = self.create_nsd_json_file(key, couchdb_response)
		#create sim.json
		self.simfile = self.create_sim_json_file(key)
		print("----> Local json files created succesfully")
		
	#
	#Calls the SINGLETON Manager for submiting a job
	#	
	def submit_job(self):
		try:
			#url for the sim.json file arg in create_job
			root_url = "file:" + self.simfile
			#simhome is job's fileloc
			self.simhome = Manager.create_job(root_url)
		except:
			print("Failed submitting new job")	
		
		self.download_plan(self.read_json_file_argument(self.nsdfile, "plan_id"))
		self.download_project(self.read_json_file_argument(self.nsdfile, "project_id"))
		
		try:
			#get job's id
			self.retrieve_job()
			Manager.copy_simfiles(self.nsdfile, self.simfile, self.simhome)
		except:
			print("Failed copying sim and nsd files to local path")
			
	#
	#Gets the jobid by fileloc
	#
	def retrieve_job(self):
		jobs = Manager.get_jobId(self.simhome)	
		for job in jobs:
			jobid = job.jobid
		self.simjobid=jobid
		
	
	
	#
	#Creates the nsd_keyx.json file and writes 
	#the json content of the nsd file
	#downloaded from the couchdb
	#
	def create_nsd_json_file(self, key, json_data):
		nsd_json_filename = resource_path() + "nsd_" + str(key) + ".json"
		jsonfile = open(nsd_json_filename, 'w+')
		json.dump(json_data, jsonfile)
		jsonfile.close()
		return nsd_json_filename

	#
	#Creates sim.json file, necessary for a
	#monitor job to start
	#
	def create_sim_json_file(self, key):
		nsd_filename = resource_path() + "nsd_" + str(key) + ".json"
		sim_json_filename = resource_path() + "sim_" + str(key) + ".json"
		nsd_id = self.read_json_file_argument(nsd_filename, "_id")
		plan_id = self.read_json_file_argument(nsd_filename, "plan_id")
		project_id = self.read_json_file_argument(nsd_filename, "project_id")
		jsonfile = open(sim_json_filename, "w+")
		jsonfile.write("{\n")
		string = '	"nsd_id"' + ":" + '"' + str(nsd_id) + '"' + "," + "\n"
		jsonfile.write(string)
		string = '	"plan_id"' + ":" + '"' + str(plan_id) + '"' + "," + "\n"
		jsonfile.write(string)
		string = '	"project_id"' + ":" + '"' + str(project_id) + '"' + "," + "\n"
		jsonfile.write(string)
		string = '	"name"' + ":" + ' "test_sim"' + "," + "\n"
		jsonfile.write(string)
		string = '	"generator"' + ":" + ' "Castalia"' + "," + "\n"
		jsonfile.write(string)
		string = '	"nsd":' + ' "file:nsd_' + str(key) + '.json"' + "\n"
		jsonfile.write(string)
		jsonfile.write("}\n")
		jsonfile.close()
		return sim_json_filename	
		
	#
	#Reads a @argument from a json @filename
	#
	def read_json_file_argument(self, filename, argument):
		json_data = open(filename)
		data = json.load(json_data)
		json_data.close()
		try:
			value = data[argument]
			return value
		except:
			print("Requested json argument does not exist")	
	
	#
	#Downloads plan file which included in the submitted nsd file
	#
	def download_plan(self, planid):
		plan_filename = self.simhome+"/plan.json"
		try:
			planfile = self.pt_connector.download_doc(planid)
			print("----> Plan file downloaded successfully FILE:", planid)
		except:
			print("----> Plan file download failed::FILE",planid)
		try:
			jsonfile = open(plan_filename, 'w+')
			json.dump(planfile, jsonfile)
			jsonfile.close()
			print("----> Plan file created successfully FILE:",plan_filename)
		except:
			print("----> Failed creating local plan file:",plan_filename)
	
	#
	#Downloads project file which included in the submitted nsd file
	#
	def download_project(self, project_id):
		project_filename = self.simhome+"/project.json"
		try:
			projectfile = self.pt_connector.download_doc(project_id)
			print("----> Project file downloaded successfully FILE:", project_id)
		except:
			print("----> Project file download failed::FILE", project_id)
		try:
			jsonfile = open(project_filename, 'w+')
			json.dump(projectfile, jsonfile)
			jsonfile.close()
			print("----> Project file created successfully FILE:",project_filename)
		except:
			print("----> Failed creating local project file:",project_filename)


