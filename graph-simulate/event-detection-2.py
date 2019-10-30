#!/usr/bin/python3

import numpy as np
import networkx as nx
import main as simulate
import analyze
import random
import collections
import multiprocessing as mp
import itertools
import os
import graph as graphutils
from constants import INTERVAL, SIMULATION_DURATION

NUM_NODES=20
LINK_RANGE=0.4
DETECT_RANGE=0.5*LINK_RANGE

max_topo_seed = 100
max_offset_seed = 100
max_event_seed = 100

algo = {}
algo["description"] = "solo2-alpha-87"
algo["type"] = "solo2"
algo["alpha"] = 87

topo_seeds = list(range(max_topo_seed))
offset_seeds = list(range(max_offset_seed))
event_seeds = list(range(max_event_seed))


""" Filepath related functions.
"""
def graph_dirname():
    return "%s/graphs" % algo["description"]


def coord_dirname():
    return "%s/coords" % algo["description"]


def log_dirname():
    return "%s/logs" % algo["description"]


def offset_dirname():
    return "%s/offsets" % algo["description"]


def detectable_dirname():
    return "%s/detectables" % algo["description"]


def graph_filename_from_seed(topo_seed):
    return os.path.join(graph_dirname(), "graph-%d.txt" % topo_seed)


def coord_filename_from_seed(topo_seed):
    return os.path.join(coord_dirname(), "graph-%d.txt" % topo_seed)


def log_filename_from_seed(topo_seed, offset_seed):
    filename = "graph-%d/offset-%d.txt" % (topo_seed, offset_seed)
    return os.path.join(log_dirname(), filename)


def offset_filename_from_seed(topo_seed, offset_seed):
    filename = "graph-%d/offset-%d.txt" % (topo_seed, offset_seed)
    return os.path.join(offset_dirname(), filename)


def detectable_filename_from_seed(topo_seed, offset_seed, event_seed):
    filename = "graph-%d/offset-%d/event-%d.txt" \
                % (topo_seed, offset_seed, event_seed)
    return os.path.join(detectable_dirname(), filename)


def worst_latency_filename(root_dir):
    return "%s/worst-latency.txt" % root_dir 


""" File system preparation.
"""
def construct_graphs_directory():
    os.makedirs(graph_dirname(), exist_ok=True)


def construct_coords_directory():
    os.makedirs(coord_dirname(), exist_ok=True)


def construct_subdirs_by_seeds(rootdir, seeds, prefix):
    subdirs = [os.path.join(rootdir, "%s-%d" % (prefix, i)) for i in seeds]
    for sd in subdirs: 
        os.makedirs(sd, exist_ok=True)
    return subdirs


def construct_logs_directory(topo_seeds):
    os.makedirs(log_dirname(), exist_ok=True)
    construct_subdirs_by_seeds(log_dirname(), topo_seeds, prefix="graph")


def construct_offsets_directory(topo_seeds):
    os.makedirs(offset_dirname(), exist_ok=True)
    construct_subdirs_by_seeds(offset_dirname(), topo_seeds, prefix="graph")


def construct_detectable_directory(topo_seeds, offset_seeds):
    root = detectable_dirname()
    os.makedirs(root, exist_ok=True)
    subdirs = construct_subdirs_by_seeds(root, topo_seeds, prefix="graph")
    for sd in subdirs:
        construct_subdirs_by_seeds(sd, offset_seeds, prefix="offset")


def construct_directories(topo_seeds, offsets_seeds):
    construct_graphs_directory()
    construct_coords_directory()
    construct_logs_directory(topo_seeds)
    construct_offsets_directory(topo_seeds)
    construct_detectable_directory(topo_seeds, offset_seeds)


""" Graph generation related functions.
"""
def save_positions(graph, filename):
    with open(filename, "w") as fo:
        for node_id in graph:
            pos = graph.nodes[node_id]["pos"]
            fo.write("%d,%f,%f\n" % (node_id, pos[0], pos[1]))


def detectable_nodes(positions, point, detect_range):
    np_positions = np.array(positions)
    x_diff = np_positions[:, 0] - point[0]
    y_diff = np_positions[:, 1] - point[1]
    diff = np.stack((x_diff, y_diff))
    distances = np.linalg.norm(diff, ord=2, axis=0)
    in_reach = distances <= detect_range
    return [ind for ind in np.argwhere(in_reach).flatten()]


def make_graph(topo_seed):
    graph_file = graph_filename_from_seed(topo_seed)
    coord_file = coord_filename_from_seed(topo_seed)
    
    if os.path.exists(graph_file) and os.path.exists(coord_file):
        return

    graph = nx.random_geometric_graph(NUM_NODES, LINK_RANGE, seed=topo_seed)
    graph = graphutils.convert_nodes_to_integers(graph)
    
    nx.write_adjlist(graph, graph_file)
    save_positions(graph, coord_file)


def make_graphs_in_parallel(topo_seeds, nproc=8):
    with mp.Pool(nproc) as pool:
        graph_list = pool.map(make_graph, topo_seeds)


""" Offset generation related functions.
"""
def assign_offsets(args):
    topo_seed = args[0]
    offset_seed = args[1]

    graph_file = graph_filename_from_seed(topo_seed)
    log_file = log_filename_from_seed(topo_seed, offset_seed)
    offset_file = offset_filename_from_seed(topo_seed, offset_seed)

    if os.path.exists(offset_file):
        return
    
    if algo["description"] == "random":
        random.seed(offset_seed)
        graph = nx.read_adjlist(graph_file)
        graph = graphutils.convert_nodes_to_integers(graph)
        offset_dict = {n: random.randint(0, INTERVAL - 1) for n in graph}
    elif algo["description"] == "sync":
        graph = nx.read_adjlist(graph_file)
        graph = graphutils.convert_nodes_to_integers(graph)
        offset_dict = {n: 0 for n in graph}

    else:
        simulate.test_instance(graph_file, offset_seed, algo, log_file)
        max_time = analyze.examine_converge_time(log_file)
        offset_dict = analyze.examine_final_offsets(log_file)
        if max_time > 80 * INTERVAL:
            for node_id in offset_dict:
                offset_dict[node_id] = -1

    with open(offset_file, "w") as fo:
        for node_id in sorted(offset_dict):
            fo.write(str(node_id) + "," + str(offset_dict[node_id]) + "\n")


def assign_offsets_in_parallel(topo_seeds, offset_seeds, nproc=8):
    args_list = [(ts, os) for ts in topo_seeds for os in offset_seeds]
    with mp.Pool(nproc) as pool:
        pool.map(assign_offsets, args_list)


""" Event detection related functions.
"""
def read_coordinates_dict(coord_file):
    coordinates = {}
    with open(coord_file) as fo:
        for line in fo:
            row = line.rstrip().split(",")
            node_id = int(row[0])
            x_coord = float(row[1])
            y_coord = float(row[2])
            coordinates[node_id] = [x_coord, y_coord]
    return coordinates


def read_coordinates(coord_file):
    coordinates = read_coordinates_dict(coord_file)
    return [coordinates[node_id] for node_id in sorted(coordinates)]


def bounding_box_from_coordinates(coordinates):
    x_min = float("inf")
    x_max = float("-inf")
    y_min = float("inf")
    y_max = float("-inf")
    for point in coordinates:
        if point[0] < x_min:
            x_min = point[0]
        if point[0] > x_max:
            x_max = point[0]
        if point[1] < y_min:
            y_min = point[1]
        if point[1] > y_max:
            y_max = point[1]
    return x_min, x_max, y_min, y_max


def read_offsets(offset_file):
    offsets = {}
    with open(offset_file) as fo:  
        for line in fo:
            row = line.rstrip().split(",")
            node_id = int(row[0])
            offset = int(row[1])
            offsets[node_id] = offset
    return [offsets[node_id] for node_id in sorted(offsets)]


def drop_event_location(bbox, event_seed):
    random.seed(event_seed)
    return [random.uniform(bbox[0], bbox[1]), random.uniform(bbox[2], bbox[3])]


def detectable_offsets(coordinates, offsets, event_point):
    dnodes = detectable_nodes(coordinates, event_point, DETECT_RANGE)
    dnode_offsets = {d: offsets[d] for d in dnodes}
    return dnode_offsets


def detect_events(args):
    topo_seed = args[0]
    offset_seed = args[1]
    event_seed = args[2]

    offset_file = offset_filename_from_seed(topo_seed, offset_seed)
    coord_file = coord_filename_from_seed(topo_seed)
    detectable_file = detectable_filename_from_seed(topo_seed, offset_seed,
                                                    event_seed)

    if os.path.exists(detectable_file):
        return 

    dnode_offsets = {}
    offsets = read_offsets(offset_file)
    if offsets[0] != -1:
        coordinates = read_coordinates(coord_file)
        bbox = bounding_box_from_coordinates(coordinates)
        event_point = drop_event_location(bbox, event_seed)
        dnode_offsets = detectable_offsets(coordinates, offsets, event_point)

    if len(dnode_offsets) == 0:
        dnode_offsets = {-1: -1} 
    
    dnode_offsets = [(k, v) for k, v in dnode_offsets.items()]
    dnode_offsets = sorted(dnode_offsets, key=lambda t: t[1])
    assert(len(dnode_offsets) > 0)
    with open(detectable_file, "w") as fo:
        fo.write("".join(["%d,%d\n" % (k, v) for k, v in dnode_offsets]))


def detect_events_in_parallel(topo_seeds, offset_seeds, event_seeds,
                              nproc=8):
    args_list = list(itertools.product(topo_seeds, offset_seeds, event_seeds))
    with mp.Pool(nproc) as pool:
        pool.map(detect_events, args_list)


def worst_latency(args):
    topo_seed = args[0]
    offset_seed = args[1]
    event_seed = args[2]

    detectable_file = detectable_filename_from_seed(topo_seed, offset_seed,
                                                    event_seed)
    dnode_offsets = {}
    with open(detectable_file) as fo:
        for line in fo:
            row = line.rstrip().split(",")
            node_id = int(row[0])
            offset = int(row[1])
            dnode_offsets[node_id] = offset
    
    if -1 in dnode_offsets:
        return -1
    
    dnode_offsets = sorted(list(dnode_offsets.values()))
    if len(dnode_offsets) == 1:
        return INTERVAL

    dnode_offsets += [dnode_offsets[0]]
    gaps = np.remainder(np.diff(np.array(dnode_offsets) + INTERVAL), INTERVAL)
    latency = np.amax(gaps)
    assert(latency > 0)
    return latency


def worst_latency_in_parallel(topo_seeds, offset_seeds, event_seeds,
                              nproc=8):
    latency_filename = worst_latency_filename(algo["description"])
    if os.path.exists(latency_filename):
        return

    args_list = list(itertools.product(topo_seeds, offset_seeds, event_seeds))
    with mp.Pool(nproc) as pool:
        latency = pool.map(worst_latency, args_list)

    string = ""
    for seed_tup, l in zip(args_list, latency):
        string += "%d,%d,%d,%d\n" % (*seed_tup, l)

    with open(latency_filename, "w") as fo:
        fo.write(string) 


""" Auxiliary
"""
def read_worst_latency_file(root_dir):
    latencies = {} 
    with open(worst_latency_filename(root_dir)) as fo:
        for line in fo:
            row = line.rstrip().split(",")
            key = ",".join(row[:-1])
            value = int(row[-1])
            latencies[key] = value
    return latencies


def worst_latency_gain(root1, root2):
    root1_latencies = read_worst_latency_file(root1)
    root2_latencies = read_worst_latency_file(root2)
    
    keys = []
    gains = []
    for key in root1_latencies:
        if root1_latencies[key] == -1 or root2_latencies[key] == -1:
            continue
        keys.append(key) 
        gains.append(root2_latencies[key]/root1_latencies[key])

    for q in [0, 25, 50, 75, 90, 99, 99.9, 100]:
        print(q, np.percentile(gains, q))
    
    with open("gains.txt", "w") as fo:
        fo.write("".join(["%s,%f\n" % (k, g) for k, g in zip(keys, gains)]))


def display_event(topo_seed, event_seed):
    import matplotlib.pyplot as plt
    
    graph = nx.read_adjlist("solo2-alpha-87/graphs/graph-%d.txt" % topo_seed)
    graph = graphutils.convert_nodes_to_integers(graph)
    coords = read_coordinates_dict("solo2-alpha-87/coords/graph-%d.txt" % topo_seed)

    nx.draw_networkx(graph, pos=coords)
    
    bbox = bounding_box_from_coordinates(list(coords.values()))
    event_point = drop_event_location(bbox, event_seed)
    plt.plot([event_point[0]], [event_point[1]], 'x', color="red",
            markersize=10)
    circle = plt.Circle(event_point, DETECT_RANGE, facecolor="None", edgecolor="red")
    plt.gca().add_artist(circle)

    plt.show()



""" Main function.
"""
def main(algorithm):
    import time
    
    global algo 
    algo["description"] = algorithm
    
    print("algorithm:", algo["description"])

    construct_directories(topo_seeds, offset_seeds)

    start = time.time()
    make_graphs_in_parallel(topo_seeds, nproc=8)
    end = time.time()
    print("Made graphs.", end - start)

    start = time.time()
    assign_offsets_in_parallel(topo_seeds, offset_seeds, nproc=8)
    end = time.time()
    print("Assigned offsets.", end - start)

    start = time.time()
    detect_events_in_parallel(topo_seeds, offset_seeds, event_seeds, 8)
    end = time.time()
    print("Identified detectable nodes", end - start)

    start = time.time()
    worst_latency_in_parallel(topo_seeds, offset_seeds, event_seeds, 8)
    end = time.time()
    print("Calculated worst-case latencies.", end - start)



if __name__=="__main__":
    #main("random")
    #main("solo2-alpha-87")
    #worst_latency_gain("random", "solo2-alpha-87")
    display_event(36, 60)
