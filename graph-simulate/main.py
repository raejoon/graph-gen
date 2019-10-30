import argparse
import os, sys
import random
import itertools
import multiprocessing as mp
import networkx as nx
import pqueue as pq
import sleepwell, solo, solo2, desync
import graph as graphutils
from constants import INTERVAL, SIMULATION_DURATION

"""
Usage:
    ./main.py --graph-dir DIR --seed-list FILE --algo STRING --outdir DIR
    ./main.py --graph-dir DIR --seed INTEGER --algo STRING --outdir DIR
    ./main.py --graph FILE1 --seed INTEGER --algo STRING --outdir DIR \
            --alpha 0.5
"""


def save_parameters(parameters, outdir):
    params_file = os.path.join(outdir, "parameters.txt")
    with open(params_file, "w") as fo:
        fo.write(parameters + "\n")


def test_instance(graph_file, seed, algorithm, output_file):
    graph = nx.read_adjlist(graph_file)
    graph = graphutils.convert_nodes_to_integers(graph)

    random.seed(seed)

    if algorithm["type"] == "sleepwell":
        Node = sleepwell.SleepWellNode
    elif algorithm["type"] == "solo":
        Node = solo.SoloNode
        solo.ALPHA = algorithm["alpha"]
    elif algorithm["type"] == "solo2":
        Node = solo2.SoloNode
        solo2.ALPHA = algorithm["alpha"]
    elif algorithm["type"] == "desync":
        Node = desync.DesyncNode
        desync.ALPHA = algorithm["alpha"]

    queue = pq.PriorityQueue()
    num_nodes = len(graph)
    offset_list = [random.randint(0, INTERVAL - 1) for _ in range(num_nodes)]
    node_list = [Node(i, queue) for i in range(num_nodes)]

    for i, node in enumerate(node_list):
        node.set_links([node_list[j] for j in graph.neighbors(i)])
        queue.add_task((node.start, (None,)), offset_list[i])
    
    while queue.current < SIMULATION_DURATION:
        func, argv = queue.pop_task()
        func(*argv)
    
    log = []
    for i, node in enumerate(node_list):
        log += node.log
    log = sorted(log)
    log = ["%d,%d,%s,%s" % tup for tup in log]

    with open(output_file, "w") as fo:
        fo.write("\n".join(log) + "\n")

    print("Log saved in ./%s." % output_file)


def test_single_graph(graph_file, seed_list, algorithm, outdir):
    file_list = [None for _ in range(len(seed_list))]
    for i, seed in enumerate(seed_list):
        file_list[i] = "seed-%d.txt" % seed
        output_file = os.path.join(outdir, file_list[i])
        test_instance(graph_file, seed, algorithm, output_file)
    
    index_file = os.path.join(outdir, "index.txt")
    with open(index_file, "w") as fo:
        fo.write("\n".join(file_list) + "\n")


def test_multiple_graphs_serial(graph_dir, seed_list, algorithm, outdir):
    in_index_file = os.path.join(graph_dir, "index.txt")
    with open(in_index_file) as fo:
        indices = [int(line) for line in fo]
    
    file_list = [None for _ in range(len(indices) * len(seed_list))]
    cnt = 0
    for graph_id in indices:
        graph_file = os.path.join(graph_dir, str(graph_id) + ".txt")
        for seed in seed_list:
            file_list[cnt] = "graph-%d-seed-%d.txt" % (graph_id, seed)
            output_file = os.path.join(outdir, file_list[cnt])
            test_instance(graph_file, seed, algorithm, output_file)
            cnt += 1
    
    out_index_file = os.path.join(outdir, "index.txt")
    with open(out_index_file, "w") as fo:
        fo.write("\n".join(file_list) + "\n")


def test_multiple_graphs(graph_dir, seed_list, algorithm, outdir):
    index_file = os.path.join(graph_dir, "index.txt")
    with open(index_file) as fo:
        indices = [int(line) for line in fo]
    
    results = []
    with mp.Pool(processes=8) as pool:
        file_list = [None for _ in range(len(indices) * len(seed_list))]
        cnt = 0
        for graph_id in indices:
            graph_file = os.path.join(graph_dir, str(graph_id) + ".txt")
            for seed in seed_list:
                file_list[cnt] = "graph-%d-seed-%d.txt" % (graph_id, seed)
                output_file = os.path.join(outdir, file_list[cnt])
                args = (graph_file, seed, algorithm, output_file,)
                results.append(pool.apply_async(test_instance, args))
                cnt += 1
        
        for res in results:
            res.get()

    out_index_file = os.path.join(outdir, "index.txt")
    with open(out_index_file, "w") as fo:
        fo.write("\n".join(file_list) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                description="Simulate desynchronization algorithms.")
    graph_group = parser.add_mutually_exclusive_group(required=True)
    graph_group.add_argument("--graph-dir", 
                             help="directory containing graph files")
    graph_group.add_argument("--graph", 
                             help="file storing networkx adjacency list")

    seed_group = parser.add_mutually_exclusive_group(required=True)
    seed_group.add_argument("--seed-list", 
                            help="file containing ints per line")
    seed_group.add_argument("--seed", type=int,
                            help="integer for random offsets")

    parser.add_argument("--outdir", required=True,
                        help="output directory")
    parser.add_argument("--algo", required=True, 
                        choices=["sleepwell", "solo", "solo2", "desync"],
                        help="string indicating the algorithm")
    parser.add_argument("--alpha", type=int,
                        help="alpha parameter for solo, solo2, desync " +
                             "(0 < a < 100)")

    args = parser.parse_args()
    
    args.outdir = os.path.normpath(args.outdir)
    if not os.path.isdir(args.outdir):
        parser.error("%s does not exist." % args.outdir) 
    if os.listdir(args.outdir): 
        parser.error("%s is not empty." % args.outdir)

    if args.graph is not None and not os.path.isfile(args.graph):
        parser.error("./%s is not a regular file." % args.graph)
    elif args.graph_dir is not None and not os.path.isdir(args.graph_dir):
        parser.error("./%s is not a directory." % args.graph)

    if args.algo in ["solo", "solo2", "desync"] and args.alpha is None:
        parser.error("%s needs --alpha." % args.algo)
    elif args.algo == "sleepwell" and args.alpha is not None:
        print("--alpha is ignored with --algo %s" % args.algo)
    elif args.alpha <= 0 or args.alpha >= 100:
        parser.error("--alpha should be greater than 0 and less than 100")

    parameters = " ".join(sys.argv[1:])
    save_parameters(parameters, args.outdir)

    if args.seed_list is not None:
        with open(args.seed_list) as fo:
            seed_list = [int(line) for line in fo]
    else:
        seed_list = [args.seed]

    algo = {"type": args.algo}
    if args.alpha is not None:
        algo["alpha"] = args.alpha

    if args.graph_dir is not None:
        test_multiple_graphs(args.graph_dir, seed_list, algo, args.outdir)
    else:
        test_single_graph(args.graph, seed_list, algo, args.outdir)
            

    
