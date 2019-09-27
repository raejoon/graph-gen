import argparse
import os, sys
import random
import itertools
import networkx as nx

"""
Usage:
    ./main.py --graph-dir DIR --seed-list FILE --algo STRING --outdir DIR
    ./main.py --graph-dir DIR --seed INTEGER --algo STRING --outdir DIR
    ./main.py --graph FILE1 --seed INTEGER --algo STRING --outdir DIR
"""

def save_parameters(parameters, outdir):
    params_file = os.path.join(outdir, "parameters.txt")
    with open(params_file, "w") as fo:
        fo.write(parameters + "\n")


def test_single_graph(graph_file, seed, algorithm, output_file):
    graph = nx.read_adjlist(graph_file)
    graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")

    #random.seed(seed)

    #if algorithm == "sleepwell":
    #    Node = sleepwell.Sleepwell

    #queue = PriorityQueue()
    #num_nodes = len(graph)
    #offset_list = [random.randint(0, INTERVAL - 1) for _ in range(num_nodes)]
    #node_list = [Node(i, offset_list[i], queue) for i in range(num_nodes)]

    #for i, node in enumerate(node_list):
    #    node.set_neighbors([node_list[j] for j in graph.neighbors(i)])
    #
    #while queue.current < SIMULATION_DURATION:
    #    func, argv = queue.pop_task()
    #    func(*argv)

    with open(output_file, "w") as fo:
        fo.write("hello!\n");


def test_multiple_graphs(graph_dir, seed_list, algorithm, outdir):
    index_file = os.path.join(graph_dir, "index.txt")
    with open(index_file) as fo:
        indices = [int(line) for line in fo]

    for graph_id in indices:
        graph_file = os.path.join(graph_dir, str(graph_id) + ".txt")
        for seed in seed_list:
            output_file = "graph-%d-seed-%d.txt" % (graph_id, seed)
            output_file = os.path.join(outdir, output_file)
            test_single_graph(graph_file, seed, algorithm, output_file)



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

    parser.add_argument("--algo", required=True, choices=["sleepwell"],
                        help="string indicating the algorithm")

    args = parser.parse_args()

    if not os.path.isdir(args.outdir):
        parser.error("./%s does not exist." % args.outdir) 
    if os.listdir(args.outdir): 
        parser.error("./%s is not empty." % args.outdir)

    parameters = " ".join(sys.argv[1:])
    save_parameters(parameters, args.outdir)

    if args.seed_list is not None:
        with open(args.seed_list) as fo:
            seed_list = [int(line) for line in fo]
    else:
        seed_list = [args.seed]

    if args.graph_dir is not None:
        test_multiple_graphs(args.graph_dir, seed_list, args.algo, args.outdir)
    else:
        test_single_graph(args.graph, seed_list, args.algo, args.outdir)
    
