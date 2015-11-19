#!/bin/bash

files=()
for sample in "Gtt" "ttbarInc" "ttbarExc" "Wsherpa" "Zsherpa" "dijet" "data" "singletop" "topEW" "diboson"
do
  files+=($(find ./TA02_MBJ13V4-6/"${sample}"_0L/fetch/data-optimizationTree/*.root -print0 | xargs -0))
done

baseDir="Presel"
rm -rf $baseDir
mkdir -p $baseDir

supercutsLocation="supercuts/Presel.json"

outputNMinus1="n-1/Presel"
python do_n-1_cuts.py ${files[*]} --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json -f
