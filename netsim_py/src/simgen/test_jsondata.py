
import os.path
import json
from models.nsd import NSD, Network, Mote, MoteType, Position
from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia
import pdb


def test_read_plan(datastore, nsd):
		planid=nsd.plan_id
		plan=datastore.get_plan(planid)
		print("----------------------------------------------------------------------")
		print("Simulations:", plan["simulations"])
		for i in range (0, int(nsd.numOfNodes)):
			print("NodeId:",plan['NodePosition'][i]['nodeId'])
			print("Node x_coordinate:",plan['NodePosition'][i]['coordinates'][0])
			print("Node y_coordinate:",plan['NodePosition'][i]['coordinates'][1])       
			print("Node z_coordinate:",plan['NodePosition'][i]['coordinates'][2])
			print("Elevation of Ground:",plan['NodePosition'][i]['elevOfGround'])
			print("RF_Antenna_conf:", plan['NodePosition'][i]['rfAntennaConf']) 
			

def test_motedata(mote):
	print("MoteID:",mote.node_id)
	print("Position:",mote.position)
	print("MoteRole:",mote.moteRole)
	print("Elevation:",mote.elevation)
	print("RxThreshold:",mote.rx_threshold)
	print("RF_Antenna_conf:",mote.rf_antenna_conf)			
