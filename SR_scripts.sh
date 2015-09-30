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
  python do_n-1_cuts.py $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json -f

  rm -rf $cutsLocation
  python optimize.py cut $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation -o $cutsLocation --numpy -v -b

  for lumi in 1 2 4 10
  do
    significancesLocation="SR${i}Significances_${lumi}"
    rm -rf $significancesLocation

    python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory $cutsLocation -b --o $significancesLocation --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi $lumi

    outputHashLocation="outputHash_SR${i}_${lumi}"
    rm -rf $outputHashLocation

    python write_all_optimal_cuts.py --supercuts $supercutsLocation --significances $significancesLocation -o $outputHashLocation

    outputFilePlots="SR${i}_${lumi}"
    python graph-grid.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --cutdir $cutsLocation
    python graph-cuts.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --supercuts $supercutsLocation --hashdir $outputHashLocation
  done
done

for lumi in 1 2 4 10
do
  python find_optimal_signal_region.py --lumi $lumi
done
