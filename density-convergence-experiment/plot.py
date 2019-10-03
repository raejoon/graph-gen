import os
import re
import collections
import numpy as np
import matplotlib.pyplot as plt

INTERVAL = 100*1e6

def get_size_to_results(filepath):
    graph_dir = "./graphs"
    index_file = os.path.join(graph_dir, "index.txt")
    with open(index_file) as fo:
        index_list = [int(line.rstrip()) for line in fo]
    
    graph_to_size = {}
    for graph_ind in index_list:
        graph_file = os.path.join(graph_dir, str(graph_ind) + ".txt")
        with open(graph_file) as fo:
            count = len([line for line in fo if line[0] != "#"])
            graph_to_size[graph_ind] = count
    
    results = collections.defaultdict(list)
    with open(filepath) as fo:
        for line in fo:
            graph_file, converge_time = line.split()
            graph_file = os.path.basename(graph_file)
            graph_index = int(re.search(r'\d+', graph_file).group())
            size = graph_to_size[graph_index]
            results[size].append(float(converge_time))

    return results 


def get_size_to_success_rate(size_to_results):
    size_to_success = {}
    for size, time_list in size_to_results.items():
        total = len(time_list)
        success = len([t for t in time_list if t != float("inf")])
        rate = success / total * 100
        size_to_success[size] = rate
    return size_to_success


def get_size_to_time_stats(size_to_results):
    size_to_time_stats = {}
    for size, time_list in size_to_results.items():
        success = [t / INTERVAL for t in time_list if t != float("inf")]
        size_to_time_stats[size] = (np.mean(success), np.std(success))
    return size_to_time_stats


sleepwell_results = \
        get_size_to_results("analysis/sleepwell-convergence-time.txt")

sleepwell_success_rate = \
        get_size_to_success_rate(sleepwell_results)

sleepwell_time_stats = \
        get_size_to_time_stats(sleepwell_results)


solo_results = \
        get_size_to_results("analysis/solo-convergence-time.txt")

solo_success_rate = \
        get_size_to_success_rate(solo_results)

solo_time_stats = \
        get_size_to_time_stats(solo_results)


def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        height_str = "100" if height == 100. else "%.1f" % height
        plt.gca().text(rect.get_x() + rect.get_width() / 2,
                       height + 0.3, 
                       height_str, ha='center', va='bottom')

def autolabel2(rects, errors):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for i, rect in enumerate(rects):
        height = rect.get_height()
        height_str = "100" if height == 100. else "%.2f" % height
        plt.gca().text(rect.get_x() + rect.get_width() / 2, 
                       height + errors[i] + 0.3,
                       height_str, ha='center', va='bottom')


sizes = sorted(list(sleepwell_success_rate.keys()))
labels = [str(s) for s in sizes]
x = np.arange(len(labels))
width = 0.35

plt.figure()

sleepwell_success_rates = [sleepwell_success_rate[k] for k in sizes]
solo_success_rates = [solo_success_rate[k] for k in sizes]

rects1 = plt.bar(x - width/2, sleepwell_success_rates, width, color="grey",
                 edgecolor="grey", label="SleepWell")
rects2 = plt.bar(x + width/2, solo_success_rates, width, color="white",
                 edgecolor="grey", label="Solo")

plt.ylabel("Instances that converge within 50 intervals (%)")
plt.xlabel("Size of complete (fully-connected) graph")
plt.xticks(x)
plt.gca().set_xticklabels(labels)
plt.yticks(range(0, 120, 20))
plt.ylim(0, 120)
plt.legend(loc="upper left", ncol=2)

autolabel(rects1)
autolabel(rects2)
plt.tight_layout()
plt.savefig("figs/success-rate.pdf")

sleepwell_time_mean = [sleepwell_time_stats[k][0] for k in sizes]
sleepwell_time_std = [sleepwell_time_stats[k][1] for k in sizes]
solo_time_mean = [solo_time_stats[k][0] for k in sizes]
solo_time_std = [solo_time_stats[k][1] for k in sizes]

plt.figure()

rects1 = plt.bar(x - width/2, sleepwell_time_mean, width,
                 yerr=sleepwell_time_std, color="grey", edgecolor="grey", 
                 label="SleepWell", error_kw=dict(elinewidth=2))
rects2 = plt.bar(x + width/2, solo_time_mean, width, 
                 yerr=solo_time_std, color="white", edgecolor="grey", 
                 label="Solo", error_kw=dict(elinewidth=2))

plt.ylabel("Number of intervals to converge")
plt.xlabel("Size of complete (fully-connected) graph")

plt.xticks(x)
plt.gca().set_xticklabels(labels)
plt.legend(loc="upper left", ncol=2)

autolabel2(rects1, sleepwell_time_std)
autolabel2(rects2, solo_time_std)
plt.tight_layout()
plt.savefig("figs/converge-time.pdf")
