import numpy as np
import networkx as nx
import main as simulate
import analyze, analyze2
import random
import collections
import multiprocessing as mp
import itertools
import os
from constants import INTERVAL, SIMULATION_DURATION

NUM_NODES=20
LINK_RANGE=0.4
DETECT_RANGE=LINK_RANGE

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


def graph_filename_from_seed(topo_seed):
    return os.path.join(graph_dirname(), "graph-%d.txt" % topo_seed)


def coord_filename_from_seed(topo_seed):
    return os.path.join(coord_dirname(), "graph-%d.txt" % topo_seed)


def log_filename_from_seed(topo_seed, offset_seed):
    filename = "graph-%d-seed-%d.txt" % (topo_seed, offset_seed)
    return os.path.join(log_dirname(), filename)


def offset_filename_from_seed(topo_seed, offset_seed):
    filename = "graph-%d-seed-%d.txt" % (topo_seed, offset_seed)
    return os.path.join(offset_dirname(), filename)


def degree_filename():
    return "%s/degree.txt" % algo["description"]


def detectable_filename():
    return "%s/detectable.txt" % algo["description"]


def latency_filename():
    return "%s/latency.txt" % algo["description"]


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
    graph = nx.convert_node_labels_to_integers(G=graph, ordering="sorted")
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
        graph = nx.convert_node_labels_to_integers(G=graph, ordering="sorted")
        offset_dict = {n: random.randint(0, INTERVAL - 1) for n in graph}
    elif algo["description"] == "sync":
        graph = nx.read_adjlist(graph_file)
        graph = nx.convert_node_labels_to_integers(G=graph, ordering="sorted")
        offset_dict = {n: 0 for n in graph}

    else:
        simulate.test_instance(graph_file, offset_seed, algo, log_file)
        max_time = analyze.examine_converge_time(log_file)
        offset_dict = analyze.examine_final_offsets(log_file)
        if max_time == float("inf"):
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
    read_coordinates_dict(coord_file)
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


def make_event(event_seed):
    random.seed(event_seed)
    event_point = [random.random(), random.random()]
    event_offset = random.randint(0, INTERVAL - 1)
    return event_point, event_offset


def detect_latency(coordinates, offsets, event_point, event_offset):
    dnodes = detectable_nodes(coordinates, event_point, DETECT_RANGE)
    if len(dnodes) == 0:
        return 0, -1
    np_offsets = np.array([offsets[d] for d in dnodes])
    latencies = np.remainder(np_offsets + INTERVAL - event_offset, INTERVAL)
    return len(dnodes), np.amin(latencies)


def worst_latency(coordinates, offsets, event_point):
    dnodes = detectable_nodes(coordinates, event_point, DETECT_RANGE)
    if len(dnodes) == 0:
        return 0, -1
    dnode_offsets = sorted([offsets[d] for d in dnodes])
    dnode_offsets += [dnode_offsets[0]]
    gaps = np.remainder(np.diff(np.array(dnode_offsets) + INTERVAL), INTERVAL)
    return len(dnodes), np.amax(gaps)
    

def detect_events(args):
    topo_seed = args[0]
    offset_seed = args[1]
    event_seed = args[2]

    offset_file = offset_filename_from_seed(topo_seed, offset_seed)
    coord_file = coord_filename_from_seed(topo_seed)

    offsets = read_offsets(offset_file)
    if offsets[0] == -1:
        return -1, -1
    coordinates = read_coordinates(coord_file)
    bbox = bounding_box_from_coordinates(coordinates)
    event_point = drop_event_location(bbox, event_seed)
    #event_point, event_offset = make_event(event_seed)
    #detectables, latency = \
    #        detect_latency(coordinates, offsets, event_point, event_offset)
    detectables, latency = \
            worst_latency(coordinates, offsets, event_point)
    return detectables, latency


def detect_events_in_parallel(topo_seeds, offset_seeds, event_seeds,
                                  nproc=8):
    if os.path.exists(detectable_filename()) and \
            os.path.exists(latency_filename()):
        return

    args_list = list(itertools.product(topo_seeds, offset_seeds, event_seeds))
    with mp.Pool(nproc) as pool:
        result = pool.map(detect_events, args_list)

    detectables = [None for _ in range(len(result))]
    latencies = [None for _ in range(len(result))]
    ind = 0
    for detectable, latency in result:
        detectables[ind] = detectable
        latencies[ind] = latency
        ind += 1

    with open(detectable_filename(), "w") as fo:
        fo.write("\n".join([str(d) for d in detectables]) + "\n")

    with open(latency_filename(), "w") as fo:
        fo.write("\n".join([str(l) for l in latencies]) + "\n")


""" Analysis related functions.
"""
def latency_cdf():
    with open(latency_filename()) as fo:
        latencies = [int(line.rstrip()) for line in fo]
    latencies = [l for l in latencies if l >= 0]

    bins = np.linspace(0, INTERVAL, 10 + 1)
    hist, _ = np.histogram(latencies, bins)
    cdf = np.cumsum(hist) / len(latencies)
    print("latency", "cdf")
    for b, c in zip(bins[1:], cdf):
        print(b/INTERVAL, c)


def latency_cdf_inverse(percentile):
    with open(latency_filename()) as fo:
        latencies = [int(line.rstrip()) for line in fo]
    latencies = [l for l in latencies if l >= 0]
    
    print("percentile", "latency")
    for q in percentile:
        print(q, np.percentile(latencies, q) / INTERVAL)


def detectable_cdf():
    with open(detectable_filename()) as fo:
        detectables = [int(line.rstrip()) for line in fo]
    detectables = [l for l in detectables if l > 0]

    bins = np.linspace(0, max(detectables), 10 + 1)
    hist, _ = np.histogram(detectables, bins)
    cdf = np.cumsum(hist) / len(detectables)
    print("detectables", "cdf")
    for b, c in zip(bins[1:], cdf):
        print(b, c)


def detectable_cdf_inverse(percentile):
    with open(detectable_filename()) as fo:
        detectables = [int(line.rstrip()) for line in fo]
    detectables = [l for l in detectables if l > 0]

    print("percentile", "detectable")
    for q in percentile:
        print(q, np.percentile(detectables, q))


def degree_cdf_inverse(percentile):
    with open(degree_filename()) as fo:
        degrees = [int(line.rstrip()) for line in fo]

    print("percentile", "degree")
    for q in percentile:
        print(q, np.percentile(degrees, q))


def graph_degrees(topo_seed):
    graph_file = graph_filename_from_seed(topo_seed)
    graph = nx.read_adjlist(graph_file)
    return [tup[1] for tup in graph.degree()]


def graph_degrees_in_parallel(topo_seeds, nproc=8):
    if os.path.exists(degree_filename()):
        return
    with mp.Pool(nproc) as pool:
        results = pool.map(graph_degrees, topo_seeds)
    degrees = []
    for res in results:
        degrees += res
    
    with open(degree_filename(), "w") as fo:
        fo.write("\n".join([str(d) for d in degrees]) + "\n")


def check_solo_correctness(args):
    topo_seed = args[0]
    offset_seed = args[1]

    global algo
    algo["description"] = "solo2-alpha-87"
     
    graph_file = graph_filename_from_seed(topo_seed)
    log_file = log_filename_from_seed(topo_seed, offset_seed)
    surplus = analyze2.examine_target_separation(graph_file, log_file) 
    max_time = analyze.examine_converge_time(log_file)

    if max_time < 80 * INTERVAL:
        return 0
    else:
        return surplus


def check_solo_correctness_in_parallel(topo_seeds, offset_seeds, nproc=8):
    args_list = [(ts, os,) for ts in topo_seeds for os in offset_seeds]
    with mp.Pool(nproc) as pool:
        result = pool.map(check_solo_correctness, args_list)
    print(sorted(result)[:20])



""" Main function.
"""
def main(algorithm):
    import time
    
    global algo 
    algo["description"] = algorithm
    
    print("algorithm:", algo["description"])

    start = time.time()
    os.makedirs(graph_dirname(), exist_ok=True)
    os.makedirs(coord_dirname(), exist_ok=True)
    make_graphs_in_parallel(topo_seeds, nproc=8)
    end = time.time()
    print("Made graphs.", end - start)

    start = time.time()
    os.makedirs(log_dirname(), exist_ok=True)
    os.makedirs(offset_dirname(), exist_ok=True)
    assign_offsets_in_parallel(topo_seeds, offset_seeds, nproc=8)
    end = time.time()
    print("Assigned offsets.", end - start)

    start = time.time()
    detect_events_in_parallel(topo_seeds, offset_seeds, event_seeds, 8)
    end = time.time()
    print("Detected events.", end - start)
    
    latency_cdf_inverse([0, 25, 50, 75, 90, 99, 99.9, 100])


if __name__=="__main__":
    print("Warning!!! event-detection.py is deprecated. Use event-detection-2.py")
    main("random")
    main("solo2-alpha-87")

    graph_degrees_in_parallel(topo_seeds, nproc=8)
    degree_cdf_inverse([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    detectable_cdf_inverse([0, 25, 50, 75, 100])
    #check_solo_correctness_in_parallel(topo_seeds, offset_seeds, nproc=8)
