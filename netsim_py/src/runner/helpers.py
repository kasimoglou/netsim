import sys
import re
import os
import requests
import random
from pprint import pprint
from collections import namedtuple

filepath="/home/julie/netsim2/netsim_py/resources/testsim1/"


def create_nsd_file(response_tokens):
	key=random.randint(1,100000000)
	nsd_json_filename=filepath+"nsd_"+str(key)+".json"
	sim_json_filename=filepath+"sim_"+str(key)+".json"
	length=len(response_tokens)
	length=len(response_tokens)
	counter=0
	
	try:
		if(os.path.exists(filepath)):
			jsonfile=open(nsd_json_filename,"w+")
			jsonfile.write("{\n")
			while (counter < length-1):
				string=str(response_tokens[counter])+","+"\n"
				jsonfile.write(string)
				counter=counter+1
			string=str(response_tokens[counter])+"\n"
			jsonfile.write(string)
			jsonfile.write("}\n")
			jsonfile.close()
	except:
		print("Cannot process nsd json file")
	try:
		if(os.path.exists(filepath)):
			jsonfile=open(sim_json_filename,"w+")
			jsonfile.write("{\n")
			string='	"name"'+":"+' "test_sim"'+","+"\n"
			jsonfile.write(string)
			string='	"generator"'+":"+' "Castalia"'+","+"\n"
			jsonfile.write(string)
			string='	"nsd":'+' "file:nsd_'+str(key)+'.json"'+"\n"
			jsonfile.write(string)
			jsonfile.write("}\n")
			jsonfile.close()
	except:
		print ("Cannot process sim json file")
	return sim_json_filename


def process_nsd_response(response):
	tokens=[]
	tokens2=[]
	delimeters="{","}"
	tokens=re.split(' |}|{',response)
	tokens2=re.split(",",tokens[1])	
	return tokens2
