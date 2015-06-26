'''
    Generates json results
        
'''

__author__ = 'GeoMSK'

import json
from models.nsdplot import PlotModel
import pickle


class JsonOutput:
    def __init__(self, type, simulation_id):
        self.type = type
        self.simulation_id = simulation_id
        self.node_plot_results = []
        self.node_parameter_results = []
        self.network_plot_results = []
        self.network_parameter_results = []
        self.node_2_node_results = []

    def add_node_plot_result(self, node_plot_result):
        assert isinstance(node_plot_result, NodePlotResults_node)
        # if a node plot result with the same node id exists append to it
        t = self.__find_node_plot(node_plot_result.node_id)
        if t:
            assert isinstance(t, NodePlotResults_node)
            for res in node_plot_result.results:
                t.add_result(res)
        else:
            self.node_plot_results.append(node_plot_result)

    def add_node_parameter_result(self, node_parameter_result):
        assert isinstance(node_parameter_result, NodeParameterResults_node)
        # if a node parameter result with the same node id exists append to it
        t = self.__find_node_parameter(node_parameter_result.node_id)
        if t:
            assert isinstance(t, NodeParameterResults_node)
            for res in node_parameter_result.results:
                t.add_result(res)
        else:
            self.node_parameter_results.append(node_parameter_result)

    def add_network_plot_result(self, network_plot_result):
        assert isinstance(network_plot_result, NetworkPlotResults_node)
        self.network_plot_results.append(network_plot_result)

    def add_network_parameter_result(self, network_parameter_result):
        assert isinstance(network_parameter_result, NetworkParameterResults_node)
        self.network_parameter_results.append(network_parameter_result)

    def add_node_2_node_result(self, node_2_node_result):
        assert isinstance(node_2_node_result, Node2NodeResults_node)
        # if a node2node result with the same node ids exists append to it
        t = self.__find_node2node(node_2_node_result.node1_id, node_2_node_result.node2_id)
        if t:
            assert isinstance(t, Node2NodeResults_node)
            for par in node_2_node_result.parameters:
                t.add_parameter(par)
            for pl in node_2_node_result.plots:
                t.add_plot(pl)
        else:
            self.node_2_node_results.append(node_2_node_result)

    def __find_node_plot(self, nodeid):
        for i in self.node_plot_results:
            if i.node_id == nodeid:
                return i
        return False

    def __find_node_parameter(self, nodeid):
        for i in self.node_parameter_results:
            if i.node_id == nodeid:
                return i
        return False

    def __find_node2node(self, nodeid1, nodeid2):
        for i in self.node_2_node_results:
            if i.node1_id == nodeid1 and i.node2_id == nodeid2:
                return i
        return False

    def get_json_string(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=2)

    def get_json(self):
        return json.loads(self.get_json_string())


class NodePlotResults_node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.results = []

    def add_result(self, result):
        assert isinstance(result, NodePlotResult)
        self.results.append(result)


class NodePlotResult:
    def __init__(self, name, file_id):
        self.name = name
        self.file_id = file_id


class NodeParameterResults_node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.results = []

    def add_result(self, result):
        assert isinstance(result, NodeParameterResult)
        self.results.append(result)


class NodeParameterResult:
    def __init__(self, name, unit, value):
        self.name = name
        self.unit = unit
        self.value = value


class NetworkPlotResults_node:
    def __init__(self, name, file_id):
        self.name = name
        self.file_id = file_id


class NetworkParameterResults_node:
    def __init__(self, name, unit, value):
        self.name = name
        self.unit = unit
        self.value = value


class Node2NodeResults_node:
    def __init__(self, node1_id, node2_id):
        self.node1_id = node1_id
        self.node2_id = node2_id
        self.parameters = []
        self.plots = []

    def add_parameter(self, parameter):
        assert isinstance(parameter, Node2NodeResults_parameter)
        self.parameters.append(parameter)

    def add_plot(self, plot):
        assert isinstance(plot, Node2NodeResults_plot)
        self.plots.append(plot)


class Node2NodeResults_parameter:
    def __init__(self, name, value, unit):
        self.name = name
        self.value = value
        self.unit = unit


class Node2NodeResults_plot:
    def __init__(self, name, file_id):
        self.name = name
        self.file_id = file_id


def add_node_type_parameter(jo, p, stats):
    """
    adds the given node type parameter's (p) statistics (stats) to the specified jsonOutput object jo
    stats is the actual data for the parameter, expected format is shown below (3 columns)
    ______________
    | node | data|
    |      |     |
    """
    assert isinstance(jo, JsonOutput)
    assert isinstance(stats, list)
    assert all(isinstance(x, tuple) for x in stats)
    assert len(stats[0]) == 2  # node type stats should have 2 columns (node,data)

    # add statistic for each node to the JsonOutput object
    for row in stats:
        node = row[0]
        value = row[1]
        # create a new "node parameter result" for node n
        nprn = NodeParameterResults_node(str(node))
        # add to that "results" (name, unit, value)
        nprn.add_result(NodeParameterResult(p.title, p.unit, value))
        # add the new  "node parameter result" to the jsonOutput object
        jo.add_node_parameter_result(nprn)


def add_network_type_parameter(jo, p, stats):
    """
    adds the given network type parameter's (p) statistics (stats) to the specified jsonOutput object jo
    stats is the actual data for the parameter, expected format is shown below (1 column)
    _______
    | data|
    |     |
    """
    assert isinstance(jo, JsonOutput)
    assert isinstance(stats, list)
    assert all(isinstance(x, tuple) for x in stats)
    assert len(stats[0]) == 1  # node2node type stats should have 1 column (data)
    assert len(stats) == 1  # for network type parameters we should get only one row as result

    value = stats[0][0]
    # create and add to the JsonOutput object a new "network parameter result"
    jo.add_network_parameter_result(
        NetworkParameterResults_node(p.title, p.unit, value))


def add_node2node_type_parameter(jo, p, stats):
    """
    adds the given node2node type parameter p to the specified jsonOutput object jo
    stats is the actual data for the parameter, expected format is shown below (3 columns)
    ________________________
    | node | n_index | data|
    |      |         |     |
    """
    assert isinstance(jo, JsonOutput)
    assert isinstance(stats, list)
    assert all(isinstance(x, tuple) for x in stats)
    assert len(stats[0]) == 3  # node2node type stats should have 3 columns (node,n_index,data)

    for row in stats:
        node = row[0]
        index = row[1]
        value = row[2]

        if index == -1: continue  # a value of -1 indicates that there is no index for this statistic's value
        # create a new "node 2 node result"
        n2nr = Node2NodeResults_node(node, index)
        # create and add the new parameter to the above "node 2 node result"
        n2nr.add_parameter(Node2NodeResults_parameter(p.title, value, p.unit))
        # add n2n result to JsonOutput
        jo.add_node_2_node_result(n2nr)


def parameter2json(jo, p, stats):
    """
    adds the given parameters stats, generated from plotModel p, to the specified jsonOutput object jo
    stats is the actual data for the parameter, expected format is shown below

    Node parameter:
    ______________
    | node | data|
    |      |     |

    Node 2 Node parameter:
    ________________________
    | node | n_index | data|
    |      |         |     |

    Network parameter:
    _______
    | data|
    |     |

    """

    assert isinstance(jo, JsonOutput)
    assert isinstance(stats, list)
    assert all(isinstance(x, tuple) for x in stats)

    t_len = len(stats[0])

    if t_len == 2:  # node type parameter
        add_node_type_parameter(jo, p, stats)
    elif t_len == 1:  # network type parameter
        add_network_type_parameter(jo, p, stats)
    elif t_len == 3:  # node2node type parameter
        add_node2node_type_parameter(jo, p, stats)
    else:
        raise Exception("Unexpected results format, got %d columns, expecting 1,2 or 3" % t_len)


def plot2json(jo, plot, filename):
    """
    adds a plot to the specified json object jo, filename is the name of the plot's figure
    """
    assert isinstance(jo, JsonOutput)
    assert isinstance(plot, PlotModel)

    if plot.stat_type == "node":
        npr = NodePlotResults_node("?")  # TODO: node id ?
        npr.add_result(NodePlotResult(plot.title, filename))
        jo.add_node_plot_result(npr)
    elif plot.stat_type == "network":
        jo.add_network_plot_result(NetworkPlotResults_node(plot.title, filename))
    elif plot.stat_type == "node2node":
        n2nr = Node2NodeResults_node("?", "?")
        n2nr.add_plot(Node2NodeResults_plot(plot.title, filename))
        jo.add_node_2_node_result(n2nr)
    else:
        raise Exception("unknown plot type: \"%s\"" % plot.stat_type)


class Info4FinishStage:
    """
    Information needed to excecute the last stage (finish) of the simulation,
    where plots and parameters (statistics) are generated
    """
    def __init__(self, sim_id, castalia_data, plotModels, parameterModels):
        self.sim_id = sim_id
        self.castalia_data = castalia_data
        self.plotModels = plotModels
        self.parameterModels = parameterModels

    def dump_to_file(self, file):
        """
        dumps this class instance to specified file using pickle
        """
        with open(file, "wb") as f:
            pickle.dump(self, f)

