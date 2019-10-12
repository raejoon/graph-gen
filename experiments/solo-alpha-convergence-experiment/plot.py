#!/usr/bin/bash

import os
import matplotlib.pyplot as plt

plt.rc("font", size=18)

scale = 0.6
plt.figure(figsize=(16*scale, 6*scale))

ls = ["-", "--", ":"]
for i, alpha_int in enumerate([50, 75, 87]):
    alpha = alpha_int / 100.
    cdf_file = "analysis/solo-%d-cdf" % alpha_int

    bins = []
    values = []
    with open(cdf_file) as fo:
        for line in fo:
            bin_str, value_str = line.rstrip().split()
            bins.append(float(bin_str) / (100*1e6))
            values.append(float(value_str))
    bins = [0] + bins
    values = [0] + values
    
    label="%.2f" % alpha
    plt.plot(bins, values, linestyle=ls[i], linewidth=3, color="grey",
             label=label)

plt.legend(title="alpha", loc="lower right")
plt.xlabel("Number of rounds to converge")
plt.ylabel("CDF")
plt.ylim(0, 1)
plt.xlim(0, 50)
plt.tight_layout()

os.makedirs("figs", exist_ok=True)
plt.savefig("figs/solo-small-alpha-convergence.pdf")
