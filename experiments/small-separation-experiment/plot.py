#!/usr/bin/python3
import os
import numpy as np
import matplotlib.pyplot as plt

""" For each algorithm, it reads two files; the convergence records of each
    instance and the records of latest maximum deficit of each instance. The
    two files are cross-referenced and the instances that failed to converge
    are filtered out. The cdf of the deficit of the rest of the instances are
    plotted.
"""

def get_meaningful_deficits(algo_name):
    convergence_file = "analysis/%s-convergence" % algo_name
    deficit_file = "analysis/%s-deficit" % algo_name
    
    blacklist = set([])
    with open(convergence_file) as fo:
        for line in fo:
            row = line.rstrip().split()
            log = row[0]
            converge_time = row[1]
            if converge_time == "inf":
                blacklist.add(log)
    
    deficits = []
    with open(deficit_file) as fo:
        for line in fo:
            row = line.rstrip().split()
            log = row[0]
            deficit = float(row[1])
            if log not in blacklist:
                deficits.append(deficit) 

    return deficits


algorithms = ["sleepwell", "desync", "solo2"]
deficits = {}
max_val = float("-inf")
min_val = float("inf")
for algo in algorithms:
    deficits[algo] = get_meaningful_deficits(algo)
    algo_max = max(deficits[algo])
    algo_min = min(deficits[algo])
    if max_val < algo_max:
        max_val = algo_max
    if min_val > algo_min:
        min_val = algo_min

bins = np.linspace(min_val, max_val, 201)
cdfs = {}
for algo in algorithms:
    hist, _ = np.histogram(deficits[algo], bins)
    cdf = np.cumsum(hist) / len(deficits[algo])
    cdfs[algo] = [0] + list(cdf)


plt.rc("font", size=18)

scale = 0.6
plt.figure(figsize=(16*scale, 6*scale))
ls = [":", "--", "-"]
labels = ["SleepWell", "DESYNC", "Solo"]
for i, algo in enumerate(algorithms):
    plt.plot(bins, cdfs[algo], linestyle=ls[i], linewidth=3, color="grey",
             label=labels[i])

plt.legend(loc="upper left")
plt.xlabel("Maximum relative deficit after convergence")
plt.ylabel("CDF")
plt.ylim(0, 1)
plt.tight_layout()

os.makedirs("figs", exist_ok=True)
plt.savefig("figs/small-separation.pdf")
