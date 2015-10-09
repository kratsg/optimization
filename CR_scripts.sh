#!/bin/bash

gttFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V5/Gtt_1L/fetch/data-optimizationTree/*.root
ttbarIncFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V5/ttbar*_1L/fetch/data-optimizationTree/*410000*r6765_r6282*.root
ttbarExcFiles=${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V5/ttbar*_1L/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root

baseDir="CR"
rm -rf $baseDir
mkdir -p $baseDir

for i in 1
#for i in 1 2 3
do
  supercutsLocation="supercuts/CR-${i}.json"
  cutsLocation="${baseDir}/CR${i}Cuts"

  outputNMinus1="n-1/CR-${i}"
  python do_n-1_cuts.py $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json -f

  python optimize.py cut $gttFiles $ttbarIncFiles $ttbarExcFiles --supercuts $supercutsLocation -o $cutsLocation --numpy -v -b

  for lumi in 2 4 10
  do

    significancesLocation="${baseDir}/CR${i}Significances_${lumi}"

    python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory $cutsLocation -b --o $significancesLocation --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi $lumi

    outputHashLocation="${baseDir}/outputHash_CR${i}_${lumi}"

    python write_all_optimal_cuts.py --supercuts $supercutsLocation --significances $significancesLocation -o $outputHashLocation

    outputFilePlots="CR${i}_${lumi}"
    python graph-grid.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --cutdir $cutsLocation
    python graph-cuts.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --supercuts $supercutsLocation --hashdir $outputHashLocation
  done
done

for lumi in 2 4 10
do
  python find_optimal_control_region.py --lumi $lumi --basedir $baseDir
done
