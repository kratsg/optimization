#!/bin/bash

gttFiles=(${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root)
ttbarIncFiles=(${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root)
ttbarExcFiles=(${HOME}/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root)

bkgdUncertainty=0.3
bkgdStatUncertainty=0.3
insignificance=0.5

#for supercuts in baseline massScan fixedMassScan noTagger no_mTb
for supercuts in massScan_RC8 massScan_RC10 massScan_RC12
do
  supercutsFile="supercuts/${supercuts}.json"
  cutsLocation="${supercuts}Cuts"

  python optimize.py cut "${gttFiles[@]}" "${ttbarIncFiles[@]}" "${ttbarExcFiles[@]}" --supercuts $supercutsFile -o $cutsLocation --numpy -v -b

  for lumi in 1 2 4 10
  do
    significancesLocation="${supercuts}Significances_${lumi}"
    python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory $cutsLocation -b -o $significancesLocation --bkgdUncertainty $bkgdUncertainty --bkgdStatUncertainty $bkgdStatUncertainty --insignificance $insignificance --lumi $lumi

    outputHashLocation="outputHash_${supercuts}_${lumi}"
    python write_all_optimal_cuts.py --supercuts $supercutsFile --significances $significancesLocation -o $outputHashLocation

    outputFilePlots="${supercuts}_${lumi}"
    python graph-grid.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --cutdir $cutsLocation
    python graph-cuts.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --supercuts $supercutsFile --hashdir $outputHashLocation
  done
done
