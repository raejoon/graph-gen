import sys, argparse
import os
import numpy as np
import networkx as nx

"""
Usage:
    python3 ./main.py --small --max 6 --outdir DIR
    python3 ./main.py --udg --dim 100 --num 200 --max-seed 10 --outdir DIR
    python3 ./main.py --random --prob 0.5 --num 200 --max-seed 10 --outdir DIR
"""

def generate_small_graphs(max_size):
    return [g for g in nx.graph_atlas_g()[1:]
                if len(g) <= max_size and nx.is_connected(g)]


def generate_udg_graphs(dim, num, max_seed):
    graph_list = [None for _ in range(max_seed + 1)]
    for seed in range(max_seed + 1):
        graph = nx.random_geometric_graph(num, 1, dim=dim, seed=seed)
        graph_list[seed] = graph_list
    return graph_list
        
        
def generate_random_graphs(prob, num, max_seed):
    graph_list = [None for _ in range(max_seed + 1)]
    for seed in range(max_seed + 1):
        graph = nx.gnp_random_graph(num, prob, seed=seed)
        graph_list[seed] = graph_list
    return graph_list


def save_graph_list(graph_list, outdir):
    for i, g in enumerate(graph_list):
        graph_file = os.path.join(outdir, "%d.txt" % i)
        nx.write_adjlist(g, graph_file)
    
    index_file = os.path.join(outdir, "index.txt")
    index_list = [str(i) for i in range(len(graph_list))]
    with open(index_file, "w") as fo:
        fo.write("\n".join(index_list))

    print("%d graphs saved in ./%s" % (len(graph_list), outdir))
     

if __name__=="__main__":
    parser = argparse.ArgumentParser(
                description="Simulate desynchronization algorithms.")
    
    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument("--small", action="store_true",
                            help="Flag to generate small connected graphs")
    type_group.add_argument("--udg", action="store_true",
                            help="Flag to generate geomteric graphs")
    type_group.add_argument("--random", action="store_true",
                            help="Flag to generate Erdos-Renyi graph")

    parser.add_argument("--outdir", required=True,
                       help="Output directory")
    # small graph attributes
    parser.add_argument("--max", type=int,
                       help="Number of maximum nodes in small graphs")
    # geometric graph attributes
    parser.add_argument("--dim", type=int,
                       help="Size of the grid for UDG placement")
    # random graph attributes
    parser.add_argument("--prob", type=float,
                       help="Link probability for Erdos-Renyi graphs") 
    # randomly generated graphs
    parser.add_argument("--num", type=int,
                       help="Number of nodes for randomly generated graphs")
    parser.add_argument("--max-seed", type=int,
                       help="Max seed value for randomly generated graphs")

    args = parser.parse_args()
    if not os.path.isdir(args.outdir):
        parser.error("./%s does not exist." % args.outdir)
    if os.listdir(args.outdir):
        parser.error("./%s is not empty." % args.outdir)
    
    if args.small and (args.max is None):
        parser.error("--small requires --max.") 
    if args.udg and (None in [args.dim, args.num, args.max_seed]):
        parser.error("--udg requires --dim, --num, and --max-seed.")
    if args.random and (None in [args.prob, args.num, args.max_seed]):
        parser.error("--random requires --prob, --num, --max-seed.")

    if args.small:
        graph_list = generate_small_graphs(args.max)
    elif args.udg: 
        graph_list = generate_udg_graphs(dim, num, max_seed)
    elif args.random:
        graph_list = generate_random_graphs(prob, num, max_seed)
    
    save_graph_list(graph_list, args.outdir)
