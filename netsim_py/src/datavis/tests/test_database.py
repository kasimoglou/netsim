'''

Created on Jan 21, 2015

@author: GeoMSK
'''


import pytest
import os.path, runner.config
from models.nsdplot import Table as nsdTable, Column
from datavis.model2plots import create_table
from datavis.database import StatsDatabase


def castalia_output_file():
    return os.path.join(runner.config.resource_path(), "datavis/castalia_output.txt")


def csv_data_file():
    return os.path.join(runner.config.resource_path(), "datavis/csv_test.txt")


def node_mapping_file():
    return os.path.join(runner.config.resource_path(), "datavis/dummy_nodemap.json")


def test_createdatabase():
    d = StatsDatabase(testing=True)

    assert(d.conn is not None)
    c = d.conn.cursor()
    cc = c.execute('SELECT * FROM dataTable')
    cols = list(map(lambda x: x[0], cc.description))
    assert(cols == ['module', 'node', 'name', 'label', 'n_index', 'data'])
    d.conn.close()


def test_isint():
    assert(StatsDatabase._StatsDatabase__is_int(123.0) is True)
    assert(StatsDatabase._StatsDatabase__is_int(123.123) is False)


def test_saveoutput():
    d = StatsDatabase(testing=True)
    d._StatsDatabase__save_output("module1", 1, -1, "outputname", "simlabel", "label", 123.123, table_name="dataTable")
    c = d.conn.cursor()
    res = c.execute('SELECT * FROM dataTable').fetchall()
    assert(res[0] == ("module1", 1, "outputname", "label", -1, 123.123))
    d.conn.close()


def test_getdatatable():
    d = StatsDatabase(testing=True)
    d._StatsDatabase__save_output("module1", 1, -1, "outputname", "simlabel", "label", 123.123, table_name="dataTable")
    d._StatsDatabase__save_output("module2", 2, -1, "outputname2", "simlabel2", "label2", 1234.1234, table_name="dataTable")
    res = d.get_datatable()
    assert(res[0] == ("module1", 1, "outputname", "label", -1, 123.123))
    assert(res[1] == ("module2", 2, "outputname2", "label2", -1, 1234.1234))
    d.conn.close()


def test_readcastaliaoutput():
    data_list = [('ResourceManager', 0, 'Consumed Energy', '', -1, 6.79813),
                 ('Communication.Radio', 0, 'RX pkt breakdown', 'Failed with NO interference', -1, 96.0),
                 ('Communication.Radio', 0, 'RX pkt breakdown', 'Failed, below sensitivity', -1, 101.0),
                 ('Communication.Radio', 0, 'RX pkt breakdown', 'Received with NO interference', -1, 131.0),
                 ('Application', 0, 'Packets received per node', '', 1, 60.0),
                 ('Application', 0, 'Packets received per node', '', 2, 71.0),
                 ('Application', 0, 'Application level latency, in ms', '[0,20)', 0, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[20,40)', 1, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[40,60)', 2, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[60,80)', 3, 131.0),
                 ('Application', 0, 'Application level latency, in ms', '[80,100)', 4, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[100,120)', 5, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[120,140)', 6, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[140,160)', 7, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[160,180)', 8, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[180,200)', 9, 0.0),
                 ('Application', 0, 'Application level latency, in ms', '[200,inf)', 10, 0.0),
                 ('ResourceManager', 1, 'Consumed Energy', '', -1, 6.28785),
                 ('Communication.Radio', 1, 'TXed pkts', 'TX pkts', -1, 499.0),
                 ('ResourceManager', 2, 'Consumed Energy', '', -1, 6.28569),
                 ('Communication.Radio', 2, 'TXed pkts', 'TX pkts', -1, 499.0)]
    d = StatsDatabase(testing=True)
    d.load_data_castalia(castalia_output_file())
    dt = d.get_datatable()
    for i in data_list:
        assert(i in dt)
    d.conn.close()


def test_readcastaliaoutput_with_nodemapping():
    data_list = [('ResourceManager', 'plan0', 'Consumed Energy', '', -1, 6.79813),
                 ('Communication.Radio', 'plan0', 'RX pkt breakdown', 'Failed with NO interference', -1, 96.0),
                 ('Communication.Radio', 'plan0', 'RX pkt breakdown', 'Failed, below sensitivity', -1, 101.0),
                 ('Communication.Radio', 'plan0', 'RX pkt breakdown', 'Received with NO interference', -1, 131.0),
                 ('Application', 'plan0', 'Packets received per node', '', 'plan1', 60.0),
                 ('Application', 'plan0', 'Packets received per node', '', 'plan2', 71.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[0,20)', 0, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[20,40)', 1, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[40,60)', 2, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[60,80)', 3, 131.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[80,100)', 4, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[100,120)', 5, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[120,140)', 6, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[140,160)', 7, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[160,180)', 8, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[180,200)', 9, 0.0),
                 ('Application', 'plan0', 'Application level latency, in ms', '[200,inf)', 10, 0.0),
                 ('ResourceManager', 'plan1', 'Consumed Energy', '', -1, 6.28785),
                 ('Communication.Radio', 'plan1', 'TXed pkts', 'TX pkts', -1, 499.0),
                 ('ResourceManager', 'plan2', 'Consumed Energy', '', -1, 6.28569),
                 ('Communication.Radio', 'plan2', 'TXed pkts', 'TX pkts', -1, 499.0)]
    d = StatsDatabase(testing=True)
    d.load_data_castalia(castalia_output_file(), node_mapping_file=node_mapping_file())
    dt = d.get_datatable()
    for i in data_list:
        assert(i in dt)
    d.conn.close()


def test_readCSV():
    data_list = [('foo', 'plan1', '12345'),
                 ('bar', 'plan2', '54321')]
    table = nsdTable("csvTable", [Column("name"), Column("node"), Column("data")], csv_data_file(), "csv", ["node"])
    d = StatsDatabase(testing=True)
    create_table(d, table)
    d.load_data_csv(table, node_mapping_file())
    dt = d.execute("SELECT * FROM csvTable")

    for i in data_list:
        assert(i in dt)

    d.conn.close()


def test_createview():
    d = StatsDatabase(testing=True)
    d.load_data_castalia(castalia_output_file())
    d.create_view("test_view", "SELECT node FROM dataTable")
    c = d.conn.cursor()
    res = c.execute(d.relations["test_view"].sql_fetch_all()).fetchall()
    assert res == [(0,), (0,), (0,), (0,), (0,), (0,),
                   (0,), (0,), (0,), (0,), (0,), (0,),
                   (0,), (0,), (0,), (0,), (0,), (1,),
                   (1,), (2,), (2,)]
    #TODO check column types in Relation attributes (not yet functional)
    d.conn.close()


def test_getnodes():
    d = StatsDatabase(testing=True)
    d.load_data_castalia(castalia_output_file())
    assert d.get_nodes() == [0, 1, 2]


def test_execute_exect_one():
    db = StatsDatabase(testing=True)
    db.load_data_castalia(castalia_output_file())

    with pytest.raises(Exception):
        db.execute_expect_one("SELECT node,data FROM dataTable WHERE name = 'Consumed Energy'")

    assert db.execute_expect_one("SELECT node,data FROM dataTable WHERE name = 'Consumed Energy' AND node = 0") == (0, 6.79813)


def test_execute():
    db = StatsDatabase(testing=True)
    db.load_data_castalia(castalia_output_file())

    assert db.execute("SELECT node,data FROM dataTable WHERE name = 'Consumed Energy'") == [(0, 6.79813), (1, 6.28785), (2, 6.28569)]

