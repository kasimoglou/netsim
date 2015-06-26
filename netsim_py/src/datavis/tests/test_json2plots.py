from datavis.json2plots import *
from datavis.json2plots import ViewsPlotsDecoder
import os
from runner.config import cfg
from datavis.model2plots import create_simulation_results
import json
import pytest


def test_views_plots_decoder():
    Views = [
        #
        # View 1
        #
        {
            "name": "dataTable",

            "columns": [
                {
                    "name": "node"
                },
                {
                    "name": "name"
                },
                {
                    "name": "module"
                },
                {
                    "name": "label"
                },
                {
                    "name": "n_index"
                },
                {
                    "name": "data"
                }
            ],
            "filename": "simout.txt",
            "format": "dataTable",
            "node_mapping": ["node", "n_index"],


            "plots": [
                {
                    "model_type": "plot",
                    "stat_type": "network",
                    "unit": "",
                    "x": ["node"],
                    "y": ["data"],
                    "select": "name: \"Consumed Energy\"",
                    "title": "Consumed Energy",
                    "axes": [],
                    "style": "histogram",
                    "legend": "",
                    "xlabel": "Node",
                    "ylabel": "Energy",
                    "x_range": "",
                    "y_range": "",
                    "logscale": "",
                    "grid": "",
                    "key": ""
                }
            ]

        },
        {
            "name": "view2",
            "columns": [
                {
                    "name": "node",
                    "expression": "dataTable.node",
                },
                {
                    "name": "n_index",
                    "expression": "dataTable.n_index",
                },
                {
                    "name": "data",
                    "expression": "dataTable.data",
                }
            ],
            "base_tables": [
                "dataTable"  # no need for additional id since the table name is unique
            ],
            "table_filter": "name = \"Packets received per node\"",
            "groupby": ["node", "n_index"],  # just an example, no need to group for this view

            "plots": [
                {
                    "model_type": "parameter",
                    "stat_type": "node2node",
                    "unit": "?",
                    "x": ["node", "n_index"],
                    "y": ["data"],
                    "select": {},  # all
                    "title": "packets received per node",

                    # Not applicable to parameter type, remove/keep makes no difference
                    "axes": [],
                    "style": "",
                    "legend": "",
                    "xlabel": "",
                    "ylabel": "",
                    "x_range": "",
                    "y_range": "",
                    "logscale": "",
                    "grid": "",
                    "key": ""
                }
            ]

        }
    ]

    decoder = ViewsPlotsDecoder()
    dts, pms = decoder.decode(Views)


table = Table('foo', [Column('a'), Column('b'), Column('name'), Column('dummy')])


def test_selector_parser():
    sel_str = 'a: 1, b: greater_than(5)|less_equal(3), name: "Consumed Energy"'
    selector = SelectorParser.parse(sel_str, table)

    assert isinstance(selector, dict)
    assert all(x in selector for x in ('a', 'b', 'name'))
    assert 'dummy' not in selector
    assert selector['a'] == 1
    assert selector['b']('foo') == (greater_than(5) | less_equal(3))('foo')
    assert selector['name'] == "Consumed Energy"


def test_selector_empty():
    assert SelectorParser.parse("", table, testing=True) == {}


def test_selector_bad_function():
    with pytest.raises(ValueError):
        SelectorParser.parse("a: foo(2)", table, testing=True)


def test_selector_bad_name():
    with pytest.raises(ValueError):
        SelectorParser.parse("aa: 2", table, testing=True)


def test_selector_expression():
    sel = SelectorParser.parse("a: 3*5", table, testing=True)
    assert sel['a'] == 15


def test_selector_expression2():
    with pytest.raises(ValueError):
        SelectorParser.parse("a: less_than(b)", table, testing=True)


def test_selector_builtin():
    with pytest.raises(ValueError):
        SelectorParser.parse("a: eval('2')", table, testing=True)


def test_plot_creation_through_nsd_read(tmp_dir):
    curdir = os.getcwd()
    # change dir so that the generated plots will go into that dir
    os.chdir(tmp_dir)

    if not os.path.exists("./test_plot_creation_through_nsd_read"):
        os.mkdir("./test_plot_creation_through_nsd_read")

    os.chdir("./test_plot_creation_through_nsd_read")

    vpd = ViewsPlotsDecoder()
    filename = os.path.join(cfg.resource_path, "datavis/predefined_plots.json")
    with open(filename, "r") as f:
        json_str = f.read()
        derived_tables, plot_models = vpd.decode(json.loads(json_str)["views"])
        create_simulation_results("asdf", plot_models, os.path.join(cfg.resource_path, "datavis/castalia_output2.txt"))

    # restore the working directory to its previous value
    os.chdir(curdir)