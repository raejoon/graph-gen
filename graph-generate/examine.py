#!/usr/bin/python3
import argparse
import os
import numpy as np
import networkx as nx

"""
Usage:
    python examine.py --graph-dir DIR --diameter --max-deg --min-deg
    python examine.py --graph-dir DIR --max-deg --median-deg
"""
def print_parameters(graph_dir):
    param_file = os.path.join(graph_dir, "parameters.txt")
    with open(param_file) as fo:
        print(fo.readline())


def load_graph_list(graph_dir):
    index_file = os.path.join(graph_dir, "index.txt")
    file_list = []
    with open(index_file) as fo:
        for line in fo:
            graph_file = os.path.join(graph_dir, "%s.txt" % line.rstrip())
            file_list.append(graph_file)
    
    return [nx.read_adjlist(f) for f in file_list]


def separate_connected_components(graph_list):
    new_list = []
    for graph in graph_list:
        comps = nx.connected_components(graph)
        new_list += [nx.subgraph(graph, c) for c in comps]
    return new_list 


def examine_diameters(graph_list):
    return [nx.diameter(graph) for graph in graph_list]


def examine_max_degrees(graph_list):
    data = []
    for graph in graph_list:
        data.append(max([tup[1] for tup in graph.degree()]))
    return data


def examine_min_degrees(graph_list):
    data = []
    for graph in graph_list:
        data.append(min([tup[1] for tup in graph.degree()]))
    return data


def examine_median_degrees(graph_list):
    data = []
    for graph in graph_list:
        data.append(np.median([tup[1] for tup in graph.degree()]))
    return data


def print_stats(name, data):
    print("%s\t(avg/std) : %.3f / %.3f" % (name, np.mean(data), np.std(data)))


if __name__=="__main__":
    parser = argparse.ArgumentParser(
                description="Examine statistics of multiple graphs")
    parser.add_argument("--graph-dir", required=True,
                        help="Output directory")
    parser.add_argument("--diameter", action="store_true",
                        help="Flag to report diameter of each graph")
    parser.add_argument("--max-deg", action="store_true",
                        help="Flag to report maximum degree of each graph")
    parser.add_argument("--min-deg", action="store_true",
                        help="Flag to report minimum degree of each graph")
    parser.add_argument("--median-deg", action="store_true",
                        help="Flag to report median-degree of each graph")
    
    args = parser.parse_args()
    if not os.path.isdir(args.graph_dir):
        parser.error("./%s does not exist." % args.graph_dir)
    
    flags = [args.diameter, args.max_deg, args.min_deg, args.median_deg]
    if not any(flags):
        parser.error("Require at least one from --diameter, --max-deg, "
                     + "--min-deg, --median-deg")

    graph_list = load_graph_list(args.graph_dir)
    graph_list = separate_connected_components(graph_list)
    
    print_parameters(args.graph_dir)
    if args.diameter:
        diameters = examine_diameters(graph_list)
        print_stats("Diameter", diameters)
    if args.max_deg:
        max_degrees = examine_max_degrees(graph_list)
        print_stats("Maximum Degree", max_degrees)
    if args.median_deg:
        median_degrees = examine_median_degrees(graph_list)
        print_stats("Median Degree", median_degrees)
    if args.min_deg:
        min_degrees = examine_min_degrees(graph_list)
        print_stats("Minimum Degree", min_degrees)
