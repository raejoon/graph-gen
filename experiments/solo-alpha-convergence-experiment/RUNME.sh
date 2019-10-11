#!/bin/bash
set -e

ROOT_DIR=../../
GRAPH_DIR=./graphs/
LOG_DIR=./logs/
ANALYSIS_DIR=./analysis/
FIG_DIR=./figs/

rm -rf $GRAPH_DIR
rm -rf $ANALYSIS_DIR
rm -rf $FIG_DIR
mkdir empty_dir
rsync -a --delete empty_dir/ $LOG_DIR
rm -rf $LOG_DIR
rmdir empty_dir

mkdir $GRAPH_DIR
mkdir $LOG_DIR
mkdir $ANALYSIS_DIR
mkdir $FIG_DIR

SEED_FILE=./seeds.txt

python $ROOT_DIR/graph-generate/main.py --small --max 6 --outdir $GRAPH_DIR
echo "Generated small graphs."

seq 0 999 > $SEED_FILE
echo "Generated seed file."

for ALPHA in 50 75 87;
do
    ALPHA_DIR=./logs/solo-$ALPHA
    mkdir -p $ALPHA_DIR
    python $ROOT_DIR/graph-simulate/main.py --graph-dir $GRAPH_DIR \
        --outdir $ALPHA_DIR --seed-list $SEED_FILE --algo solo2 --alpha $ALPHA
    
    ANALYSIS_FILE=$ANALYSIS_DIR/solo-$ALPHA
    python $ROOT_DIR/graph-simulate/analyze.py --logdir $ALPHA_DIR \
        --converge-time --outfile $ANALYSIS_FILE

    CDF_FILE=$ANALYSIS_DIR/solo-$ALPHA-cdf
    python $ROOT_DIR/graph-simulate/analyze.py --logdir $ALPHA_DIR \
        --converge-time --cdf --outfile $CDF_FILE

    echo "Analyzed ALPHA=$ALPHA"
done

python plot.py
