#!/usr/bin/python3
import argparse
import os
import numpy as np
import networkx as nx
import multiprocessing as mp

"""
Usage:
    python examine.py --graph-dir DIR --diameter --max-deg --min-deg
    python examine.py --graph-dir DIR --max-deg --median-deg --parallel 4
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


def connected_count(graph):
    return len(list(nx.connected_components(graph)))


def size(graph):
    return len(graph)


def diameter(graph):
    return nx.diameter(graph)


def max_degree(graph):
    return max([tup[1] for tup in graph.degree()])


def min_degree(graph):
    return min([tup[1] for tup in graph.degree()])


def median_degree(graph):
    return np.median([tup[1] for tup in graph.degree()])


def examine_stats(func, graph_list, nproc):
    if nproc == 1:
        return [func(graph) for graph in graph_list]
    
    with mp.Pool(processes=nproc) as pool:
        return pool.map(func, graph_list)    


def print_stats(name, data):
    print("%s\t(avg/std) : %.3f / %.3f" % (name, np.mean(data), np.std(data)))


if __name__=="__main__":
    parser = argparse.ArgumentParser(
                description="Examine statistics of multiple graphs")
    parser.add_argument("--graph-dir", required=True,
                        help="Output directory")
    parser.add_argument("--diameter", action="store_true",
                        help="Flag to report diameter of each graph")
    parser.add_argument("--connected-count", action="store_true",
                        help="Flag to report number of " +
                             "connected components of each graph.")
    parser.add_argument("--connected-size", action="store_true",
                        help="Flag to report size of " +
                             "each connected component.")
    parser.add_argument("--max-deg", action="store_true",
                        help="Flag to report maximum degree of each graph")
    parser.add_argument("--min-deg", action="store_true",
                        help="Flag to report minimum degree of each graph")
    parser.add_argument("--median-deg", action="store_true",
                        help="Flag to report median-degree of each graph")
    parser.add_argument("--parallel", type=int, default=1,
                        help="Number of processes to use. (default: 1)")
    
    args = parser.parse_args()
    if not os.path.isdir(args.graph_dir):
        parser.error("./%s does not exist." % args.graph_dir)
    
    flags = [args.diameter, args.connected_count, args.connected_size, 
             args.max_deg, args.min_deg, args.median_deg]
    if not any(flags):
        parser.error("Require at least one from --diameter, " +
                     "--connected-count, --connected-size, " +
                     "--max-deg, --min-deg, --median-deg")

    graph_list = load_graph_list(args.graph_dir)
    subgraph_list = separate_connected_components(graph_list)
    
    print_parameters(args.graph_dir)
    if args.diameter:
        diameters = examine_stats(diameter, subgraph_list, args.parallel)
        print_stats("Diameter", diameters)
    if args.connected_count:
        counts = examine_stats(connected_count, graph_list, args.parallel)
        print_stats("Connected Count", counts)
    if args.connected_size:
        sizes = examine_stats(size, subgraph_list, args.parallel)
        print_stats("Connected Size", sizes)
    if args.max_deg:
        max_degrees = examine_stats(max_degree, subgraph_list, args.parallel)
        print_stats("Maximum Degree", max_degrees)
    if args.median_deg:
        median_degrees = \
            examine_stats(median_degree, subgraph_list, args.parallel)
        print_stats("Median Degree", median_degrees)
    if args.min_deg:
        min_degrees = examine_stats(min_degree, subgraph_list, args.parallel)
        print_stats("Minimum Degree", min_degrees)
