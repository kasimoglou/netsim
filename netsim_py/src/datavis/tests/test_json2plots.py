from datavis.json2plots import *
from datavis.predefined_plots import PlotsEncoder
import json


def test_views_plots_decoder():
    Views = [
        #
        # View 1
        #
        {
            "name": "dataTable",  # not an actual view, this already exists in the database, used here to define plots

            ####### can be ignored/omitted for "dataTable"#######
            "columns": [  # not required since columns in dataTable are hardcoded

            ],
            "base_tables": [],  # None, this is the table that all views will derive from
            "table_filter": "",  # not required, we are not generating this table it already exists
            "groupby": [],  # not required
            ####### ------------------------------------- #######


            "plots": [
                {
                    "model_type": "plot",
                    "stat_type": "network",
                    "unit": "",
                    "x": ["node"],
                    "y": ["data"],
                    "select": "name = \"Consumed Energy\"",
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
                    "select": "",  # all
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

    dts, pms = views_plots_decoder(Views)

    for dt in dts:
        dt_j = json.dumps(dt, cls=PlotsEncoder, indent=2)
        print(dt_j)

    for pm in pms:
        pm_j = json.dumps(pm, cls=PlotsEncoder, indent=2)
        print(pm_j)

    # assert 0  # just to see the prints