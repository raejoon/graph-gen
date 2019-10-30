#!/usr/bin/python3

import numpy as np
import networkx as nx
from constants import INTERVAL


def examine_final_offsets(logfile):
    offsets = {}
    with open(logfile) as fo:
        for line in fo:
            if "init" in line:
                node_id = int(line.split(",")[1])
                offsets[node_id] = None
            elif "broadcast" in line:
                values = line.split(",")
                timestamp = int(values[0])
                node_id = int(values[1])
                offsets[node_id] = timestamp % INTERVAL
    return offsets


def examine_target_separation(graphfile, logfile):
    graph = nx.read_adjlist(graphfile)
    graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")
    offsets = examine_final_offsets(logfile) 

    surplus = []
    for node_id in graph: 
        peers = np.array([offsets[i] for i in graph.neighbors(node_id)])
        if len(peers) == 0:
            continue
        diffs = np.remainder(peers + INTERVAL - offsets[node_id], INTERVAL)
        share = np.amin(diffs)
        
        target = INTERVAL // (len(peers) + 1)
        surplus.append((share - target) / target)
    return min(surplus)
