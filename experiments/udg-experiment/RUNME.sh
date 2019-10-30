#!/bin/bash
set -e

ROOT_DIR=../../
GRAPH_DIR=./graphs/
LOG_DIR=./logs/
ANALYSIS_DIR=./analysis/
FIG_DIR=./figs/

SEED_FILE=./seeds.txt

#rm -rf $GRAPH_DIR
#rm -rf $ANALYSIS_DIR
#rm -rf $FIG_DIR
#mkdir empty_dir
#rsync -a --delete empty_dir/ $LOG_DIR
#rm -rf $LOG_DIR
#rmdir empty_dir
#
#mkdir $GRAPH_DIR
#mkdir $LOG_DIR
#mkdir $ANALYSIS_DIR
#mkdir $FIG_DIR
#
#echo "Reset files."
#
#python $ROOT_DIR/graph-generate/main.py --udg --radius 0.04 \
#    --num 1000 --max-seed 100 --outdir $GRAPH_DIR
#echo "Generated unit disk graphs."
#
#seq 0 9 > $SEED_FILE
#echo "Generated seed file."

for ALGO in sleepwell;
do
    ALGO_DIR=./logs/$ALGO
    mkdir -p $ALGO_DIR
    python $ROOT_DIR/graph-simulate/main.py --graph-dir $GRAPH_DIR \
        --outdir $ALGO_DIR --seed-list $SEED_FILE --algo $ALGO --alpha 87
    
    ANALYSIS_FILE=$ANALYSIS_DIR/$ALGO
    python $ROOT_DIR/graph-simulate/analyze.py --logdir $ALGO_DIR \
        --converge-time --outfile $ANALYSIS_FILE

    CDF_FILE=$ANALYSIS_DIR/$ALGO-cdf
    python $ROOT_DIR/graph-simulate/analyze.py --logdir $ALGO_DIR \
        --converge-time --cdf --outfile $CDF_FILE

    echo "Analyzed ALGO=$ALGO"
done

python plot.py
