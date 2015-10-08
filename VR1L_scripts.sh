#!/bin/bash

gttFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V4/Gtt_1L/fetch/data-optimizationTree/*.root
ttbarIncFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V4/ttbar*_1L/fetch/data-optimizationTree/*410000*r6765_r6282*.root
ttbarExcFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V4/ttbar*_1L/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root

for i in 1 2 3
do
  supercutsLocation="supercuts/VR1L-${i}.json"
  cutsLocation="VR1L${i}Cuts"

  outputNMinus1="n-1/VR1L-${i}"
  rm -rf $outputNMinus1
  mkdir -p $outputNMinus1
  python do_n-1_cuts.py $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json -f

  rm -rf $cutsLocation
  python optimize.py cut $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation -o $cutsLocation --numpy -v -b

  for lumi in 2 4 10
  do

    significancesLocation="VR1L${i}Significances_${lumi}"

    rm -rf $significancesLocation

    python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory $cutsLocation -b --o $significancesLocation --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi $lumi

    outputHashLocation="outputHash_VR1L${i}_${lumi}"

    rm -rf $outputHashLocation

    python write_all_optimal_cuts.py --supercuts $supercutsLocation --significances $significancesLocation -o $outputHashLocation

    outputFilePlots="VR1L${i}_${lumi}"
    python graph-grid.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --cutdir $cutsLocation
    python graph-cuts.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --supercuts $supercutsLocation --hashdir $outputHashLocation
  done
done
