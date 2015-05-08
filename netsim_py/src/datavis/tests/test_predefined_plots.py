from datavis.predefined_plots import *
from datavis.model2plots import create_simulation_results
import os
from runner.config import cfg


def generate_predef_plots(path, predef_plots):
    """
    Generate plots defined in predef_plots in the folder specified by path
    predef_plots should be of type PredefinedPlot
    """
    assert all(isinstance(x, PredefinedPlot) for x in predef_plots)
    curdir = os.getcwd()
    # change dir so that the generated plots will go into that dir
    os.chdir(path)

    plot_models = list(map(lambda x: x.plot, predef_plots))
    create_simulation_results("asdf", plot_models, os.path.join(cfg.resource_path, "datavis/castalia_output2.txt"))

    # restore the working directory to its previous value
    os.chdir(curdir)


def test_network_plot(tmp_dir):
    plot_models = [consumed_energy_per_node,

                   # TunableMAC packet breakdown
                   Received_from_App_per_node,
                   received_beacons_per_node,
                   received_data_pkts_per_node,
                   sent_beacons_per_node,
                   sent_data_pkts_per_node,

                   # RX pkt breakdown
                   Failed_with_NO_interference,
                   Failed_with_interference,
                   Failed_below_sensitivity,
                   Failed_non_RX_state,
                   Received_despite_interference,
                   Received_with_NO_interference,

                   # TXed pkts
                   TX_pkts]

    generate_predef_plots(tmp_dir, plot_models)


def test_stat_breakdown(tmp_dir):

    plot_models = [# Packet Breakdowns
                   RX_pkt_breakdown,
                   TunableMAC_packet_breakdown]

    generate_predef_plots(tmp_dir, plot_models)


def test_stat_breakdown_sum(tmp_dir):

    plot_models = [RX_pkt_breakdown_sum,
                   TunableMAC_packet_breakdown_sum]

    generate_predef_plots(tmp_dir, plot_models)


def test_predef_to_json():
    # TODO: test incomplete
    print(RX_pkt_breakdown_sum.plot_to_json_string())
    print(RX_pkt_breakdown_sum.views_to_json_string())
    # assert 0 # just to see the prints