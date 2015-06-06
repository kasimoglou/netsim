__author__ = 'George Mantakos'

from datavis.results2json import *
from models.nsdplot import Operator, EQ, ColumnRef, ConstantExpr, DATA_TABLE, DerivedTable,\
    Column, ColumnExpr, SUM, MINUS, LAND
import os.path
import hashlib
from datavis.database import StatsDatabase
from datavis.tests.test_database import castalia_output_file
from datavis.model2plots import create_view_for_derived, create_plot_for_model
from runner.config import cfg

def test_JsonOutput():
    jo = JsonOutput("simulation_results", "SIM1391536771845")

    # Node Plot Results
    npr1 = NodePlotResults_node("node_09489")
    npr1.add_result(NodePlotResult("CPU usage during simulation time", "node_result1.jpg"))
    npr1.add_result(NodePlotResult("Battery lifetime during simulation time", "node_result2.gif"))

    npr2 = NodePlotResults_node("node_09490")
    npr2.add_result(NodePlotResult("CPU usage during simulation time", "node_result3.jpg"))
    npr2.add_result(NodePlotResult("Battery lifetime during simulation time", "node_result4.gif"))

    jo.add_node_plot_result(npr1)
    jo.add_node_plot_result(npr2)

    # Node parameter Results
    npr1 = NodeParameterResults_node("node_09489")
    npr1.add_result(NodeParameterResult("Total number of messages received during simulation", "", "98787"))
    npr1.add_result(NodeParameterResult("Mean message transmission time", "second", "1.34"))

    npr2 = NodeParameterResults_node("node_09490")
    npr2.add_result(NodeParameterResult("Total number of messages received during simulation", "", "98754"))
    npr2.add_result(NodeParameterResult("Mean message transmission time", "second", "1.20"))

    jo.add_node_parameter_result(npr1)
    jo.add_node_parameter_result(npr2)

    # Network Plot Results
    jo.add_network_plot_result(NetworkPlotResults_node("Number of messages being transmitted during simulation time", "network_plot.jpg"))
    jo.add_network_plot_result(NetworkPlotResults_node("Mean network CPU usage during simulation time", "network_plot2.jpg"))

    # Network Parameter Results
    jo.add_network_parameter_result(
        NetworkParameterResults_node("Mean number of messages lost per node during simulation", "messages", "7685"))
    jo.add_network_parameter_result(
        NetworkParameterResults_node("Mean message transmission time per node", "second", "0.97"))

    # Node 2 Node Results
    n2nr1 = Node2NodeResults_node("node_09489", "node_09490")
    n2nr1.add_parameter(Node2NodeResults_parameter("Number of exchanged messages", "34", "messages"))
    n2nr1.add_parameter(Node2NodeResults_parameter("Mean message transmission time between the two nodes", "0.212", "sec"))
    n2nr1.add_plot(Node2NodeResults_plot("Mean message exchange rate between the two nodes", "figure1.png"))
    n2nr1.add_plot(Node2NodeResults_plot("Mean message loss rate between the two nodes", "figure2.png"))

    n2nr2 = Node2NodeResults_node("node_09489", "node_09491")
    n2nr2.add_parameter(Node2NodeResults_parameter("Number of exchanged messages", "43", "messages"))
    n2nr2.add_parameter(Node2NodeResults_parameter("Mean message transmission time between the two nodes", "0.333", "sec"))
    n2nr2.add_plot(Node2NodeResults_plot("Mean message exchange rate between the two nodes", "figure3.png"))
    n2nr2.add_plot(Node2NodeResults_plot("Mean message loss rate between the two nodes", "figure4.png"))

    jo.add_node_2_node_result(n2nr1)
    jo.add_node_2_node_result(n2nr2)


    couchdb_example_json = '''{
       "type": "simulation_results",
       "simulation_id": "SIM1391536771845",
       "node_plot_results": [
           {
               "node_id": "node_09489",
               "results": [
                   {
                       "name": "CPU usage during simulation time",
                       "file_id": "node_result1.jpg"
                   },
                   {
                       "name": "Battery lifetime during simulation time",
                       "file_id": "node_result2.gif"
                   }
               ]
           },
           {
               "node_id": "node_09490",
               "results": [
                   {
                       "name": "CPU usage during simulation time",
                       "file_id": "node_result3.jpg"
                   },
                   {
                       "name": "Battery lifetime during simulation time",
                       "file_id": "node_result4.gif"
                   }
               ]
           }
       ],
       "node_parameter_results": [
           {
               "node_id": "node_09489",
               "results": [
                   {
                       "name": "Total number of messages received during simulation",
                       "unit": "",
                       "value": "98787"
                   },
                   {
                       "name": "Mean message transmission time",
                       "unit": "second",
                       "value": "1.34"
                   }
               ]
           },
           {
               "node_id": "node_09490",
               "results": [
                   {
                       "name": "Total number of messages received during simulation",
                       "unit": "",
                       "value": "98754"
                   },
                   {
                       "name": "Mean message transmission time",
                       "unit": "second",
                       "value": "1.20"
                   }
               ]
           }
       ],
       "network_plot_results": [
           {
               "name": "Number of messages being transmitted during simulation time",
               "file_id": "network_plot.jpg"
           },
           {
               "name": "Mean network CPU usage during simulation time",
               "file_id": "network_plot2.jpg"
           }
       ],
       "network_parameter_results": [
           {
               "name": "Mean number of messages lost per node during simulation",
               "unit": "messages",
               "value": "7685"
           },
           {
               "name": "Mean message transmission time per node",
               "unit": "second",
               "value": "0.97"
           }
       ],
       "node_2_node_results": [
           {
               "node1_id": "node_09489",
               "node2_id": "node_09490",
               "parameters": [
                   {
                       "name": "Number of exchanged messages",
                       "value": "34",
                       "unit": "messages"
                   },
                   {
                       "name": "Mean message transmission time between the two nodes",
                       "value": "0.212",
                       "unit": "sec"
                   }
               ],
               "plots": [
                   {
                       "name": "Mean message exchange rate between the two nodes",
                       "file_id": "figure1.png"
                   },
                   {
                       "name": "Mean message loss rate between the two nodes",
                       "file_id": "figure2.png"
                   }
               ]
           },
           {
               "node1_id": "node_09489",
               "node2_id": "node_09491",
               "parameters": [
                   {
                       "name": "Number of exchanged messages",
                       "value": "43",
                       "unit": "messages"
                   },
                   {
                       "name": "Mean message transmission time between the two nodes",
                       "value": "0.333",
                       "unit": "sec"
                   }
               ],
               "plots": [
                   {
                       "name": "Mean message exchange rate between the two nodes",
                       "file_id": "figure3.png"
                   },
                   {
                       "name": "Mean message loss rate between the two nodes",
                       "file_id": "figure4.png"
                   }
               ]
           }]
    }'''

    assert json.loads(couchdb_example_json) == json.loads(jo.get_json_string())


def test_add_node_type_parameter():
    db = StatsDatabase()
    db.load_castalia_output(castalia_output_file())

    # node parameter
    q = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Consumed Energy\"")])
    rel = DerivedTable("test", [Column("node"), Column("data")], [DATA_TABLE], q)
    create_view_for_derived(db, rel)
    pm_node = PlotModel("parameter", "node", rel, (rel.col["node"],), (rel.col["data"],),
                        select={"name": "Consumed Energy"}, title="Consumed Energy")

    # create JsonOutput object
    jo = JsonOutput("simulation_results", "243241234143141")

    # fetch stats from db
    stats = db.execute("SELECT node, data FROM dataTable WHERE name = \"Consumed Energy\"")

    # add parameters to jsonOutput object
    add_node_type_parameter(jo, pm_node, stats)

    correct_json = """{
  "node_2_node_results": [],
  "node_parameter_results": [
    {
      "results": [
        {
          "name": "Consumed Energy",
          "unit": "",
          "value": 6.79813
        }
      ],
      "node_id": "0"
    },
    {
      "results": [
        {
          "name": "Consumed Energy",
          "unit": "",
          "value": 6.28785
        }
      ],
      "node_id": "1"
    },
    {
      "results": [
        {
          "name": "Consumed Energy",
          "unit": "",
          "value": 6.28569
        }
      ],
      "node_id": "2"
    }
  ],
  "simulation_id": "243241234143141",
  "node_plot_results": [],
  "type": "simulation_results",
  "network_plot_results": [],
  "network_parameter_results": []
}"""

    assert json.loads(correct_json) == json.loads(jo.get_json_string())


def test_add_network_type_parameter():
    db = StatsDatabase()
    db.load_castalia_output(castalia_output_file())

    # column name
    c_name = Column("name")
    # column SUM(data) AS data
    c_data = ColumnExpr("data", Operator(SUM, [ConstantExpr("data")]))
    # filter --> name = "Consumed Energy"
    f = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Consumed Energy\"")])
    # create derived table containing the SUM of all "Consumed Energy"
    dt = DerivedTable("dt", [c_name, c_data], [DATA_TABLE], f, [DATA_TABLE.col["name"]])

    # generate a view based on the above derived table
    create_view_for_derived(db, dt)

    # network parameter
    pm_node = PlotModel("parameter", "network", dt, None, (dt.col["data"],), title="Total Consumed Energy")

    # create JsonOutput object
    jo = JsonOutput("simulation_results", "46345634563456")

    # fetch stats from db
    stats = db.execute("SELECT data FROM dt")

    # add parameter to jsonOutput object
    add_network_type_parameter(jo, pm_node, stats)

    correct_json = """{
  "node_parameter_results": [],
  "node_plot_results": [],
  "node_2_node_results": [],
  "network_parameter_results": [
    {
      "value": 19.371669999999998,
      "unit": "",
      "name": "Total Consumed Energy"
    }
  ],
  "type": "simulation_results",
  "network_plot_results": [],
  "simulation_id": "46345634563456"
}"""

    assert json.loads(correct_json) == json.loads(jo.get_json_string())


def test_add_node2node_type_parameter():
    db = StatsDatabase()
    db.load_castalia_output(castalia_output_file())

    # DerivedTable for node2node parameter
    q = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Packets received per node\"")])
    dt = DerivedTable("testn2n", [Column("node"), Column("n_index"), Column("data")], [DATA_TABLE], q)

    # node2node parameter
    pm_node = PlotModel("parameter", "node2node", dt, (dt.col["node"], dt.col["n_index"]), (dt.col["data"],),
                        title="Packets received per node")

    # generate a view based on the above derived table
    create_view_for_derived(db, dt)

    # create JsonOutput object
    jo = JsonOutput("simulation_results", "5678657421")

    # fetch stats from db
    stats = db.execute("SELECT node,n_index,data FROM testn2n")

    # add parameter to jsonOutput object
    add_node2node_type_parameter(jo, pm_node, stats)

    correct_json = """{
  "network_parameter_results": [],
  "node_plot_results": [],
  "network_plot_results": [],
  "simulation_id": "5678657421",
  "type": "simulation_results",
  "node_parameter_results": [],
  "node_2_node_results": [
    {
      "plots": [],
      "node2_id": 1,
      "node1_id": 0,
      "parameters": [
        {
          "name": "Packets received per node",
          "value": 60.0,
          "unit": ""
        }
      ]
    },
    {
      "plots": [],
      "node2_id": 2,
      "node1_id": 0,
      "parameters": [
        {
          "name": "Packets received per node",
          "value": 71.0,
          "unit": ""
        }
      ]
    }
  ]
}"""

    assert json.loads(correct_json) == json.loads(jo.get_json_string())


def test_plot2json():
    #name = "Consumed Energy"
    ds = StatsDatabase()
    ds.load_castalia_output(castalia_output_file())
    table_filter = Operator(EQ, [ColumnRef(DATA_TABLE.columns[3]), ConstantExpr("\"Consumed Energy\"")])
    dt = DerivedTable("test_plot2json1", [Column("node"), Column("data"), Column("name")], [DATA_TABLE], table_filter)
    create_view_for_derived(ds, dt)
    x = DATA_TABLE.col["node"]
    y = DATA_TABLE.col["data"]
    axes = None
    select = {"name": "Consumed Energy"}  # all ?

    # create a plotmodel based on the above info
    pm1 = PlotModel("plot", "network", dt, (x,), (y,), axes, select, title="node over data")

    # dummy plot model for testing
    pm2 = PlotModel("plot", "node", dt, (x,), (y,), axes, select, title="node over data")

    # create JsonOutput object
    jo = JsonOutput("simulation_results", "07987986875")

    plot2json(jo, pm1, "file1")
    plot2json(jo, pm2, "file2")

    correct_json = '''{
  "type": "simulation_results",
  "node_parameter_results": [],
  "simulation_id": "07987986875",
  "node_2_node_results": [],
  "network_parameter_results": [],
  "network_plot_results": [
    {
      "name": "node over data",
      "file_id": "file1"
    }
  ],
  "node_plot_results": [
    {
      "results": [
        {
          "name": "node over data",
          "file_id": "file2"
        }
      ],
      "node_id": "?"
    }
  ]
}'''

    assert json.loads(correct_json) == json.loads(jo.get_json_string())


class executor_final_stage_test:
    @staticmethod
    def get_plot_models():
        table_filter = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Consumed Energy\"")])
        dt = DerivedTable("test_plotModel2json1", [Column("node"), Column("data"), Column("name")], [DATA_TABLE], table_filter)
        x = DATA_TABLE.col["node"]
        y = DATA_TABLE.col["data"]
        axes = None
        select = {"name": "Consumed Energy"}  # all ?

        # create a plotmodel based on the above info
        pm1 = PlotModel("plot", "network", dt, (x,), (y,), axes, select)

        # node parameter
        q = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Consumed Energy\"")])
        dt = DerivedTable("test", [Column("node"), Column("data")], [DATA_TABLE], q)
        pm_node1 = PlotModel("parameter", "node", dt, (dt.col["node"],), (dt.col["data"],),
                             title="Consumed Energy")

        # DerivedTable for Network parameter
        # column SUM(data) AS data
        c_data = ColumnExpr("data", Operator(SUM, [ConstantExpr("data")]))
        # filter --> name = "Consumed Energy"
        f = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Consumed Energy\"")])
        # create derived table containing the SUM of all "Consumed Energy"
        dt2 = DerivedTable("dt", [c_data], [DATA_TABLE], f)

        # network parameter
        pm_node2 = PlotModel("parameter", "network", dt2, None, (dt.col["data"],),
                             title="Total Consumed Energy")

        # DerivedTable for node2node parameter
        q = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("\"Packets received per node\"")])
        dt3 = DerivedTable("testn2n", [Column("node"), Column("n_index"), Column("data")], [DATA_TABLE], q)

        # node2node parameter
        pm_node3 = PlotModel("parameter", "node2node", dt3, (dt3.col["node"], dt3.col["n_index"]), (dt3.col["data"],),
                             title="Packets received per node")

        return [pm1, pm_node1, pm_node2, pm_node3]


    @staticmethod
    def get_castalia_data():
        return os.path.join(cfg.resource_path, "datavis/castalia_output.txt")

