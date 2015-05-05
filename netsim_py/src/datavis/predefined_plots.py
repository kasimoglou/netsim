from models.nsdplot import PlotModel, DATA_TABLE, DerivedTable, Column, Operator, EQ, ColumnRef, ConstantExpr, ColumnExpr, \
    SUM
import json
from datavis.model2plots import expression2sql


class PlotsEncoder(json.JSONEncoder):
    """
    custom encoder to handle PlotModel and DerivedTable
    """
    def default(self, obj):
        if isinstance(obj, PlotModel):
            return {
                "model_type": obj.model_type,
                "stat_type": obj.stat_type,
                "rel": obj.rel.name,
                "x": [col.name for col in obj.x],
                "y": [col.name for col in obj.y],
                "axes": obj.axes,
                "select": obj.select,
                "title": obj.title,
                "style": obj.style,
                "legend": obj.legend,
                "xlabel": obj.xlabel,
                "ylabel": obj.ylabel,
                "x_range": obj.x_range,
                "y_range": obj.y_range
            }
        elif isinstance(obj, DerivedTable):
            return {
                "name": obj.name,
                "columns": [
                    {
                        "name": c.name,
                        "parent": c.parent.name if c.parent is not None else None,
                        "table": c.table.name
                    } for c in obj.columns
                ],
                "base_tables": [t.name for t in obj.base_tables],
                "table_filter": expression2sql(obj.table_filter),
                "groupby": [c.table.name+"."+c.name for c in obj.groupby]
            }
        else:
            return json.JSONEncoder.default(self, obj)


class PredefinedPlot:
    """
    This is a template to create a plot, should be subclassed to provide more detail
    """
    def __init__(self, stat_name, stat_label=None):
        assert not (stat_name is None and stat_label is None)
        self.stat_name = stat_name
        self.stat_label = stat_label
        self.views = []   # the views required to generate the plot
        self.plot = None  # the plot to be generated

    def add_view(self, view):
        assert isinstance(view, DerivedTable)
        self.views.append(view)

    def make_plot(self, rel, x, y, model_type="plot", stat_type="network", axes=None, select={}, title=None,
                  style="linespoints", legend="DEFAULT", xlabel=None, ylabel=None, x_range=None, y_range=None,
                  logscale=None, grid=" ", key=None, unit=""):
        """
        create the PlotModel object
        """
        self.plot = PlotModel(model_type, stat_type, rel, x, y, axes, select, title, style, legend,
                              xlabel, ylabel, x_range, y_range, logscale, grid, key, unit)

    def plot_to_json_string(self):
        """
        returns this predefined plot encoded as a json string
        """
        return json.dumps(self.plot, cls=PlotsEncoder, indent=2)

    def plot_to_json(self):
        """
        returns this predefined plot encoded as a json object (python dictionary)
        """
        return self.plot.__dict__

    def views_to_json_string(self):
        """
        returns views encoded as a json string
        """
        return json.dumps(self.views, cls=PlotsEncoder, indent=2)

    def views_to_json(self):
        """
        returns views encoded as a json object (python dictionary)
        """
        return self.views.__dict__


class NetworkPlot(PredefinedPlot):
    """
    This is a template to create a simple network plot
    It describes a plot with all applicable nodes in the x axis and values of the specified statistic in the y axis
    Either/both of stat_name, stat_label must be defined
    """
    def __init__(self, stat_name=None, stat_label=None, ylabel="Data", y_range=None, title=None, style="linespoints"):
        super().__init__(stat_name, stat_label)

        # create selector
        select = {}
        if stat_name:
            select["name"] = stat_name
        if stat_label:
            select["label"] = stat_label
        # specify statistic name to be used, label or name
        name = stat_label if stat_label else stat_name

        self.make_plot(DATA_TABLE, (DATA_TABLE.col["node"],), (DATA_TABLE.col["data"],),
                       select=select, title=title if title else "%s per node" % name,
                       xlabel="Node", ylabel=ylabel, y_range=y_range, style=style)
#
# ResourceManager
#

# Consumed Energy
consumed_energy_per_node       = NetworkPlot("Consumed Energy",
                                             style="histogram")

#
# MAC
#

# TunableMAC packet breakdown
Received_from_App_per_node     = NetworkPlot(stat_label="Received from App",
                                             ylabel="Packets",
                                             style="histogram")

received_beacons_per_node      = NetworkPlot(stat_label="received beacons",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

received_data_pkts_per_node    = NetworkPlot(stat_label="received data pkts",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

sent_beacons_per_node          = NetworkPlot(stat_label="sent beacons",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

sent_data_pkts_per_node        = NetworkPlot(stat_label="sent data pkts",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

#
# Radio
#

# RX pkt breakdown
Failed_with_NO_interference    = NetworkPlot(stat_label="Failed with NO interference",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

Failed_with_interference       = NetworkPlot(stat_label="Failed with interference",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

Failed_below_sensitivity       = NetworkPlot(stat_label="Failed, below sensitivity",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

Failed_non_RX_state            = NetworkPlot(stat_label="Failed, non RX state",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

Received_despite_interference  = NetworkPlot(stat_label="Received despite interference",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

Received_with_NO_interference  = NetworkPlot(stat_label="Received with NO interference",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")

# TXed pkts
TX_pkts                        = NetworkPlot(stat_label="TX pkts",
                                             ylabel="Packets",
                                             y_range="[0:]",
                                             style="histogram")


class StatBreakdown(PredefinedPlot):
    """
    This is a template to create a "stat breakdown"
    It describes a plot with all applicable nodes in the x axis and values of the specified
    statistic labels (substatistic) in the y axis
    """
    def __init__(self, stat_name, title=None, ylabel="", y_range=None, logscale=None):
        super().__init__(stat_name)
        self.make_plot(DATA_TABLE, (DATA_TABLE.col["node"],), (DATA_TABLE.col["data"],),
                       axes=["label"], select={"name": stat_name}, title=title if title else stat_name,
                       xlabel="Node", ylabel=ylabel, y_range=y_range, style="histogram", logscale=logscale)

#
# Stat Breakdowns as histograms
#
RX_pkt_breakdown_hist            = StatBreakdown("RX pkt breakdown",
                                                 ylabel="Packets",
                                                 y_range="[0:]")

TunableMAC_packet_breakdown_hist = StatBreakdown("TunableMAC packet breakdown",
                                                 ylabel="Packets",
                                                 y_range="[0:]")


#
# Stat Breakdowns
#

RX_pkt_breakdown                 = StatBreakdown("RX pkt breakdown",
                                                 ylabel="Packets",
                                                 y_range="[0:]")

TunableMAC_packet_breakdown      = StatBreakdown("TunableMAC packet breakdown",
                                                 ylabel="Packets",
                                                 y_range="[0:]")


class StatBreakdownSum(PredefinedPlot):
    def __init__(self, stat_name, title=None, ylabel="", y_range=None, logscale=None):
        super().__init__(stat_name)
        # filter --> name = stat_name
        c_node = Column("node")
        c_data = ColumnExpr("data", Operator(SUM, [ColumnRef(DATA_TABLE.col["data"])]))
        f = Operator(EQ, [ColumnRef(DATA_TABLE.col["name"]), ConstantExpr(stat_name)])
        dt = DerivedTable("%s_stat_breakdown" % stat_name.replace(" ", "_"), [c_node, c_data], [DATA_TABLE], f, groupby=[DATA_TABLE.col["node"]])
        self.add_view(dt)

        self.make_plot(dt, (dt.col["node"],), (dt.col["data"],),
                       title=title if title else stat_name, xlabel="Node", ylabel=ylabel, y_range=y_range,
                       style="histogram", logscale=logscale)

#
# Stat Breakdown Sums
#

RX_pkt_breakdown_sum                 = StatBreakdownSum("RX pkt breakdown",
                                                        ylabel="Packets",
                                                        title="RX packets",
                                                        y_range="[0:]",)

TunableMAC_packet_breakdown_sum      = StatBreakdownSum("TunableMAC packet breakdown",
                                                        ylabel="Packets",
                                                        title="TunableMAC packets",
                                                        y_range="[0:]",)