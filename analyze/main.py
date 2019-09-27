#!/usr/bin/python3

"""
Usage:
    python main.py --logdir DIR --min-broadcast-count --outfile FILE
    python main.py --logdir DIR --converge-time --outfile FILE
    python main.py --logdir DIR --deficit --transient --outfile FILE
"""

import argparse
import os

def examine_min_broadcast_count(logfile):
    broadcasts = {}
    with open(logfile) as fo:
        for line in fo:  
            if "init" in line:
                node_id = int(line.split(",")[1])
                broadcasts[node_id] = 0
            elif "broadcast" in line:
                node_id = int(line.split(",")[1])
                broadcasts[node_id] += 1
    return min(broadcasts.values())


def examine_converge_time(logfile):
    pass

def examine_transient_deficit(logfile):
    pass


def read_file_list(logdir):
    index_file = os.path.join(logdir, "index.txt")
    with open(index_file) as fo:
        file_list = [line.rstrip() for line in fo]
        return [os.path.join(logdir, f) for f in file_list]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                description="Analyze simulation logs.")
    parser.add_argument("--logdir", required=True,
                        help="Directory containing simulation logs")
    parser.add_argument("--outfile", required=True,
                        help="Output file")
    
    stat_group = parser.add_mutually_exclusive_group(required=True)
    stat_group.add_argument("--min-broadcast-count", action="store_true",
                            help="Flag to collect minimum broadcast count")
    stat_group.add_argument("--converge-time", action="store_true",
                            help="Flag to collect converge times")
    stat_group.add_argument("--deficit", action="store_true",
                            help="Flag to collect deficits")
    
    parser.add_argument("--transient", action="store_true",
                        help="Collect deficits only in transient phase")
    
    args = parser.parse_args()
    if args.deficit is None and args.transient is not None:
        parser.error("--transient is only used with --deficit.")
    if args.deficit is not None and args.transient is None:
        parser.error("--deficit requires --transient.")
    if not os.path.isdir(args.logdir):
        parser.error("./%s does not exist." % args.logdir)

    filepath_list = read_file_list(args.logdir)
   
    if args.min_broadcast_count:
        data = [examine_min_broadcast_count(f) for f in filepath_list]

    if args.converge_time:
        data = [examine_converge_time(f) for f in filepath_list]
    
    if args.deficit and args.transient:
        data = [examine_transient_deficit(f) for f in filepath_list]
    
    with open(args.outfile, "w") as fo:
        fo.write("\n".join(str(d) for d in data) + "\n")
