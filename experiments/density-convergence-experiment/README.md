1. Generate complete graphs of size 2, 4, 8, 16, 32
```
python ../graph-generate/main.py --complete --max 32 --powers --outdir graphs
```

2. Simulate SleepWell and Solo
```
python ../graph-simulate/main.py --outdir logs/sleepwell --graph-dir graphs \
    --seed-list seeds.txt --algo sleepwell
python ../graph-simulate/main.py --outdir logs/solo --graph-dir graphs \
    --seed-list seeds.txt --algo solo
```

3. Analyze convergence
```
python ../graph-simulate/analyze.py --logdir logs/sleepwell --converge-time \
    > analysis/sleepwell-convergence-time.txt
python ../graph-simulate/analyze.py --logdir logs/solo --converge-time \
    > analysis/solo-convergence-time.txt
```

4. Plot success rate and convergence time
```
python plot.py
```
