'''

Created on Jan 30, 2015

@author: George Mantakos
'''


import pytest
import os
import hashlib
from models.nsdplot import Column
from datavis.tests.test_database import castalia_output_file
from datavis.database import StatsDatabase
from datavis.create_plot import *


#uncomment to generate a test plot
def test_plot(tmp_dir):
    curdir = os.getcwd()
    # change dir so that the generated plots will go into that dir
    os.chdir(tmp_dir)

    d = StatsDatabase()
    d.load_castalia_output(castalia_output_file())
    d.create_view("test_view", "SELECT node, name, data FROM dataTable")
    plot = make_plot(d.relations["test_view"], (Column("node"),), (Column("data"),), ["name"], select={"name": "Consumed Energy"}, terminal=PNG())
    plot.make_plot()

    # restore the working directory to its previous value
    os.chdir(curdir)

