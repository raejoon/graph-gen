#!/usr/bin/bash

import os
import matplotlib.pyplot as plt
import numpy as np

plt.rc("font", size=18)

scale = 0.6
plt.figure(figsize=(16*scale, 6*scale))

color = ["grey", "red"]
ls = ["-", "-"]

for i, algo in enumerate(["solo", "solo2"]):
    cdf_file = "analysis/%s-cdf" % algo

    bins = []
    values = []
    with open(cdf_file) as fo:
        for line in fo:
            bin_str, value_str = line.rstrip().split()
            bins.append(float(bin_str) / (100*1e6))
            values.append(float(value_str))
    bins = [0] + bins
    values = [0] + values

    label="PCO with degree-based separation" if algo == "solo" else "Fidget"
    plt.plot(bins, values, linestyle=ls[i], linewidth=3, color=color[i],
             label=label)


plt.legend(loc="lower right")
plt.xlabel("Number of rounds to converge")
plt.ylabel("CDF")
plt.ylim(0, 1)
plt.xlim(0, 50)
plt.tight_layout()

os.makedirs("figs", exist_ok=True)
plt.savefig("figs/solo-small-convergence.pdf")
