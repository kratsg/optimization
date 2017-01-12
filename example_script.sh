#!/bin/bash

# generate cuts
files=$(find /Users/kratsg/2.4.19-0-0/*.root  -not -iname "*Gbb*" -not -iname "*data*")
python ../Optimization/optimize.py cut ${files} --supercuts=supercuts/main.json -o cuts/main --numpy -b --eventWeight "event_weight" --weightsFile ../Optimization/weights.json --tree oTree

# specify signal and background dids and calculate significances
signal=$(awk '{print $1"*"}' ../massWindows_Gtt.txt | tr '\n' ' ')
bkgd=$(cat bkgdFiles | sed "s/$/.json/g" | tr '\n' ' ')
python ../Optimization/optimize.py optimize --signal $signal --bkgd $bkgd --searchDirectory=cuts/main -b --o=significances/main --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi 35

# generate a summary of your results
python ../Optimization/optimize.py summary --searchDirectory significances/main --massWindows ../massWindows_Gtt.txt --output summary_main.json

# produce a list of optimal cuts
python ../Optimization/optimize.py hash summary_main.json --supercuts supercuts/main.json -o outputHash/main --use-summary

# make the standard set of plots for significance, ratio, signal and background yields
python ../Optimization/graph-grid.py --summary summary_main.json --lumi 35 -o main --do-run1 --run1-excl run1_limit.csv --run1-1sigma run1_limit_1sigma.csv -b

# make a set of plots showing the optimal cuts
python ../Optimization/graph-cuts.py --summary summary_main.json --lumi 35 -o main --do-run1 --run1-excl run1_limit.csv --run1-1sigma run1_limit_1sigma.csv -b --outputHash outputHash/main --supercuts supercuts/main.json

# compare with another summary you made
python ../Optimization/summary-comparison.py --base-summary summary_old.json --comp-summary summary_main.json --lumi 35 -o main -b
