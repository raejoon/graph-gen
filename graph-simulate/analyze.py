#!/usr/bin/python3

"""
Usage:
    python analyze.py --logdir DIR --min-broadcast-count --outfile FILE
    python analyze.py --logdir DIR --converge-time --outfile FILE
    python analyze.py --logdir DIR --converge-time --cdf
    python analyze.py --logdir DIR --deficit --transient --outfile FILE
"""

import argparse
import os
import numpy as np
from constants import INTERVAL, SIMULATION_DURATION

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
    broadcasts = {}
    with open(logfile) as fo:
        for line in fo:
            if "init" in line:
                node_id = int(line.split(",")[1])
                broadcasts[node_id] = []
            elif "broadcast" in line:
                values = line.split(",")
                timestamp = int(values[0])
                node_id = int(values[1])
                broadcasts[node_id].append(timestamp)
    
    max_time = float("-inf")
    for node_id in broadcasts:
        error = np.abs(np.diff(broadcasts[node_id]) - INTERVAL) / INTERVAL
        for ind in range(len(error) - 1, -1, -1):
            if error[ind] > 1e-6:
                break
        converge_time = broadcasts[node_id][ind + 1]
        if ind == len(error) - 1:
            converge_time = float("inf")
        if max_time < converge_time:
            max_time = converge_time
    
    return max_time


def examine_transient_deficit(logfile):
    pass


def calculate_cdf(data, range_min, range_max, nbins):
    bins = np.linspace(range_min, range_max, nbins + 1)
    hist, bin_edges = np.histogram(data, bins)
    cdf = np.cumsum(hist) / len(data)
    return bin_edges[1:], cdf


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
    parser.add_argument("--outfile",
                        help="Output file")
    parser.add_argument("--cdf", action="store_true",
                        help="Flag to present the distribution of the stat")
    
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
    if args.converge_time is None and args.cdf is not None:
        parser.error("--cdf is only used with --converge-time.")
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
    
    if args.cdf:
        bins, cdfs = calculate_cdf(data, 0, SIMULATION_DURATION, 20)
        output_str = "\n".join("%f\t%f" % (b, c) for (b, c) in zip(bins, cdfs))
    else:
        output_str = "\n".join("%s\t%s" % (f, str(d))
                                    for f, d in zip(filepath_list, data))
    
    if args.outfile:
        with open(args.outfile, "w") as fo:
            fo.write(output_str + "\n")
    else:
        print(output_str)
