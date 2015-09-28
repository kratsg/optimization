#!/bin/bash

gttFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root
ttbarIncFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root
ttbarExcFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root

for i in 1 2 3 4
do
  supercutsLocation="supercuts/SR-${i}.json"
  cutsLocation="SR${i}Cuts"
  outputNMinus1="n-1/SR-${i}"

  rm -rf $outputNMinus1
  mkdir -p $outputNMinus1

  python do_n-1_cuts.py $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json
done


gttFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V2/Gtt_1L/fetch/data-optimizationTree/*.root
ttbarIncFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V2/ttbar*_1L/fetch/data-optimizationTree/*410000*r6765_r6282*.root
ttbarExcFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V2/ttbar*_1L/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root

for i in 1 2 3 4
do
  supercutsLocation="supercuts/CR-${i}.json"
  cutsLocation="CR${i}Cuts"
  outputNMinus1="n-1/CR-${i}"

  rm -rf $outputNMinus1
  mkdir -p $outputNMinus1

  python do_n-1_cuts.py $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json
done
