'''

Created on Feb 03, 2015

@author: George Mantakos
'''

from datavis.model2plots import collect_tables_for_pml, expression2sql, derived2sql, create_view_for_derived, \
    create_plot_for_model, model2plots
from datavis.database import less_than, StatsDatabase, Attribute, not_equal
from models.nsdplot import Table, DerivedTable, Column, ColumnExpr, ConstantExpr, ColumnRef, Operator, PlotModel, \
    PLUS, MINUS, DIV, MULT, EQ, NOTEQ, LESS, LESS_EQ, GREATER, GREATER_EQ, AVG, COUNT, FIRST, LAST, MAX, MIN, \
    SUM, LAND, LOR, DATA_TABLE
from datavis.results2json import JsonOutput
from datavis.tests.test_database import castalia_output_file
import json
import os

def test_collect_tables_for_pml():
    ca = Column("a")
    cb = Column("b")
    cc = Column("c")
    cd = Column("d")
    ce = Column("e")
    cf = Column("f")
    t = Table("t", [ca, cb, cc, cd, ce, cf])
    dt1_filter = Operator(LAND,
                          [Operator(NOTEQ, [ColumnRef(ca), ConstantExpr(0)]),
                           Operator(GREATER, [ColumnRef(ca), ConstantExpr(5)])])
    dt2_filter = Operator(LOR,
                          [Operator(LESS, [Operator(PLUS, [ColumnRef(cc), ConstantExpr(2)]), ColumnRef(cd)]),
                           Operator(LESS_EQ, [ColumnRef(cc), ConstantExpr(5)])])
    dt1 = DerivedTable("dt1", [ca, cb], [t], dt1_filter)
    dt2 = DerivedTable("dt2", [cc, cd], [t], dt2_filter, [cc])

    dt3 = DerivedTable("dt3", [ca, cd], [dt1, dt2], None)

    pml = PlotModel("plot", "network", dt3, (ca,), (cd,), ["a", "d"], {'a': less_than(0.125)})
    assert collect_tables_for_pml([pml]) == [t, dt1, dt2, dt3]


def test_expression2sql():
    def op_test(tuple_op, string):
        op = Operator(tuple_op[0], tuple_op[1])
        assert expression2sql(op) == string

    assert expression2sql(ConstantExpr(5)) == "5"
    assert expression2sql(ColumnRef(Column("test_col"))) == "test_col"
    col = Column("col")
    assert expression2sql(ColumnExpr("col", Operator(SUM, [ColumnRef(col)]))) == "SUM(col) AS col"

    # inline functions
    operands = [ColumnRef(Column("test_col")), ConstantExpr(2)]
    vs = "(test_col %s 2)"  # validation string
    op_test((PLUS, operands), vs % "+")
    op_test((MINUS, operands), vs % "-")
    op_test((DIV, operands), vs % "/")
    op_test((MULT, operands), vs % "*")
    op_test((EQ, operands), vs % "=")
    op_test((NOTEQ, operands), vs % "<>")
    op_test((LESS, operands), vs % "<")
    op_test((LESS_EQ, operands), vs % "<=")
    op_test((GREATER, operands), vs % ">")
    op_test((GREATER_EQ, operands), vs % ">=")

    operands2 = [ColumnRef(Column("test_col")), ConstantExpr(5)]
    assert expression2sql(Operator(LAND, [
        Operator(GREATER_EQ, operands),
        Operator(LESS_EQ, operands2)
    ])) == "((test_col >= 2) AND (test_col <= 5))"

    assert expression2sql(Operator(LOR, [
        Operator(GREATER_EQ, operands),
        Operator(LESS_EQ, operands2)
    ])) == "((test_col >= 2) OR (test_col <= 5))"

    #agregate functions
    operands = [ColumnRef(col)]
    vs = "%s(col)"  # validation string

    op_test((AVG, operands), vs % "AVG")
    op_test((COUNT, operands), vs % "COUNT")
    op_test((FIRST, operands), vs % "FIRST")
    op_test((LAST, operands), vs % "LAST")
    op_test((MAX, operands), vs % "MAX")
    op_test((MIN, operands), vs % "MIN")
    op_test((SUM, operands), vs % "SUM")


def dupc(col):
    return Column(col.name)


def test_derived2sql():
    ca = Column("a")
    cb = Column("b")
    cc = Column("c")
    cd = Column("d")
    ce = Column("e")
    cf = Column("f")
    t = Table("t", [ca, cb, cc, cd, ce, cf])
    dt1_filter = Operator(LAND,
                          [Operator(NOTEQ, [ColumnRef(ca), ConstantExpr(0)]),
                           Operator(GREATER, [ColumnRef(ca), ConstantExpr(5)])])
    dt2_filter = Operator(LOR,
                          [Operator(LESS, [Operator(PLUS, [ColumnRef(cc), ConstantExpr(2)]), ColumnRef(cd)]),
                           Operator(LESS_EQ, [ColumnRef(cc), ConstantExpr(5)])])
    dt1 = DerivedTable("dt1", [ca, cb], [t], dt1_filter)

    dt2 = DerivedTable("dt2", [cc, cd], [t], dt2_filter, [cc])

    dt3_filter = Operator(LOR,
                          [Operator(LESS, [Operator(PLUS, [ColumnRef(ca), ConstantExpr(2)]), ColumnRef(cd)]),
                           Operator(LESS_EQ, [ColumnRef(cd), ConstantExpr(5)])])

    dt3 = DerivedTable("dt3", [dupc(ca), dupc(cd)], [dt1, dt2], dt3_filter, [ca])

    assert derived2sql(dt1) == "SELECT a,b FROM t WHERE ((a <> 0) AND (a > 5))"
    assert derived2sql(dt2) == "SELECT c,d FROM t WHERE (((c + 2) < d) OR (c <= 5)) GROUP BY c"
    assert derived2sql(dt3) == "SELECT a,d FROM dt1,dt2 WHERE (((a + 2) < d) OR (d <= 5)) GROUP BY a"


def test_createviewforderived():
    d = StatsDatabase()
    alist = [Attribute("a", "int"),
             Attribute("b", "int"),
             Attribute("c", "int"),
             Attribute("d", "int"),
             Attribute("e", "int"),
             Attribute("f", "int"),
    ]
    ca = Column("a")
    cb = Column("b")
    cc = Column("c")
    cd = Column("d")
    ce = Column("e")
    cf = Column("f")
    t = Table("t", [ca, cb, cc, cd, ce, cf])
    d.create_table("t", alist)
    dt1_filter = Operator(LAND,
                          [Operator(NOTEQ, [ColumnRef(ca), ConstantExpr(0)]),
                           Operator(GREATER, [ColumnRef(ca), ConstantExpr(5)])])
    dt2_filter = Operator(LOR,
                          [Operator(LESS, [Operator(PLUS, [ColumnRef(cc), ConstantExpr(2)]), ColumnRef(cd)]),
                           Operator(LESS_EQ, [ColumnRef(cc), ConstantExpr(5)])])
    dt1 = DerivedTable("dt1", [ca, cb], [t], dt1_filter)
    dt2 = DerivedTable("dt2", [cc, cd], [t], dt2_filter, [cc])

    dt3_filter = Operator(LAND,
                          [Operator(LOR,
                                    [Operator(LESS, [Operator(PLUS, [ColumnRef(ca), ConstantExpr(2)]), ColumnRef(cd)]),
                                     Operator(LESS_EQ, [ColumnRef(cd), ConstantExpr(5)])
                                    ]),
                           Operator(EQ, [ColumnRef(ca), ColumnRef(cd)])
                          ])

    dt3 = DerivedTable("dt3", [dupc(ca), dupc(cd)], [dt1, dt2], dt3_filter, [ca])

    create_view_for_derived(d, dt1)
    create_view_for_derived(d, dt2)
    create_view_for_derived(d, dt3)

    assert d.relations["dt1"].name == "dt1"
    dt1_attr = d.get_attributes_of_relation("dt1")
    assert dt1_attr[0].name == "a"
    assert dt1_attr[1].name == "b"

    assert d.relations["dt2"].name == "dt2"
    dt2_attr = d.get_attributes_of_relation("dt2")
    assert dt2_attr[0].name == "c"
    assert dt2_attr[1].name == "d"

    assert d.relations["dt3"].name == "dt3"
    dt3_attr = d.get_attributes_of_relation("dt3")
    assert dt3_attr[0].name == "a"
    assert dt3_attr[1].name == "d"


def test_create_plot_for_model(tmp_dir):
    curdir = os.getcwd()
    # change dir so that the generated plots will go into that dir
    os.chdir(tmp_dir)

    jo = JsonOutput("simulation_results", "SIM1391536771845")
    #
    # network plot
    #
    #name = "Consumed Energy"
    ds = StatsDatabase()
    ds.load_castalia_output(castalia_output_file())
    table_filter = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("Consumed Energy")])
    dt = DerivedTable("test_create_plot_for_model", [Column("node"), Column("data"), Column("name")], [DATA_TABLE], table_filter)
    create_view_for_derived(ds, dt)
    x = DATA_TABLE.col["node"]
    y = DATA_TABLE.col["data"]
    axes = None
    select = {"name": "Consumed Energy"}  # all ?

    pm1 = PlotModel("plot", "network", dt, (x,), (y,), axes, select)

    #
    # node parameter
    #
    q = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("Consumed Energy")])
    rel = DerivedTable("nodepar_test", [Column("node"), Column("data")], [DATA_TABLE], q)
    create_view_for_derived(ds, rel)
    pm2 = PlotModel("parameter", "node", rel, (rel.col["node"],), (rel.col["data"],),
                        title="Consumed Energy")

    #
    # network Parameter
    #
    # column name
    c_name = Column("name")
    # column SUM(data) AS data
    c_data = ColumnExpr("data", Operator(SUM, [ConstantExpr("data")]))
    # filter --> name = "Consumed Energy"
    f = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("Consumed Energy")])
    # create derived table containing the SUM of all "Consumed Energy"
    dt = DerivedTable("networkpar_test", [c_name, c_data], [DATA_TABLE], f, [DATA_TABLE.col["name"]])

    # generate a view based on the above derived table
    create_view_for_derived(ds, dt)

    pm3 = PlotModel("parameter", "network", dt, None, (dt.col["data"],), title="Total Consumed Energy")

    #
    # node2node parameter
    #

    # DerivedTable for node2node parameter
    q = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("Packets received per node")])
    dt = DerivedTable("testn2n", [Column("node"), Column("n_index"), Column("data")], [DATA_TABLE], q)

    pm4 = PlotModel("parameter", "node2node", dt, (dt.col["node"], dt.col["n_index"]), (dt.col["data"],),
                        title="Packets received per node")

    # generate a view based on the above derived table
    create_view_for_derived(ds, dt)

    create_plot_for_model(pm1, ds, jo)
    create_plot_for_model(pm2, ds, jo)
    create_plot_for_model(pm3, ds, jo)
    create_plot_for_model(pm4, ds, jo)

    correct_json = """{
  "node_parameter_results": [
    {
      "results": [
        {
          "name": "Consumed Energy",
          "value": 6.79813,
          "unit": ""
        }
      ],
      "node_id": "0"
    },
    {
      "results": [
        {
          "name": "Consumed Energy",
          "value": 6.28785,
          "unit": ""
        }
      ],
      "node_id": "1"
    },
    {
      "results": [
        {
          "name": "Consumed Energy",
          "value": 6.28569,
          "unit": ""
        }
      ],
      "node_id": "2"
    }
  ],
  "node_2_node_results": [
    {
      "parameters": [
        {
          "unit": "",
          "name": "Packets received per node",
          "value": 60.0
        }
      ],
      "plots": [],
      "node1_id": 0,
      "node2_id": 1
    },
    {
      "parameters": [
        {
          "unit": "",
          "name": "Packets received per node",
          "value": 71.0
        }
      ],
      "plots": [],
      "node1_id": 0,
      "node2_id": 2
    }
  ],
  "network_plot_results": [
    {
      "name": "node over data",
      "file_id": "test_create_plot_for_model:data(node).WHERE.name='Consumed.Energy'.png"
    }
  ],
  "node_plot_results": [],
  "simulation_id": "SIM1391536771845",
  "network_parameter_results": [
    {
      "name": "Total Consumed Energy",
      "value": 19.371669999999998,
      "unit": ""
    }
  ],
  "type": "simulation_results"
}"""
    assert json.loads(correct_json) == json.loads(jo.get_json_string())
    # restore the working directory to its previous value
    os.chdir(curdir)


def test_model2plots(tmp_dir):
    curdir = os.getcwd()
    # change dir so that the generated plots will go into that dir
    os.chdir(tmp_dir)

    #name = "Consumed Energy"
    table_filter = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr("Consumed Energy")])
    dt = DerivedTable("test_model2plots_1", [Column("node"), Column("data"), Column("name")], [DATA_TABLE], table_filter)
    table_filter2 = Operator(EQ, [ColumnRef(DATA_TABLE.col["label"]), ConstantExpr("TX pkts")])
    dt2 = DerivedTable("test_model2plots_2", [Column("node"), Column("data"), Column("label")], [DATA_TABLE], table_filter2)

    x = DATA_TABLE.col["node"]
    y = DATA_TABLE.col["data"]
    axes = None
    select = {"name": "Consumed Energy"}  # all ?

    pm = PlotModel("plot", "network", dt, (x,), (y,), axes, select)

    x = DATA_TABLE.col["node"]
    y = DATA_TABLE.col["data"]
    axes = None
    select = {"label": "TX pkts"}  # all ?

    pm2 = PlotModel("plot", "network", dt2, (x,), (y,), axes, select)

    jo = JsonOutput("simulation_results", "SIM1391536771845")
    model2plots([pm, pm2], jo, castalia_output_file())

    # restore the working directory to its previous value
    os.chdir(curdir)