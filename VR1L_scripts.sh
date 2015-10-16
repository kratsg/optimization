#!/bin/bash

files=()
for sample in "Gtt" "ttbarInc" "ttbarExc" "Wsherpa" "Zsherpa" "dijet" "data" "singletop" "topEW"
do
  files+=($(ls ${HOME}/Dropbox/TheAccountant_dataFiles/TA01_MBJ13V8/"${sample}"_1L/fetch/data-optimizationTree/*.root))
done

baseDir="VR1L"
rm -rf $baseDir
mkdir -p $baseDir

for i in 1 2 3 4
do
  supercutsLocation="supercuts/VR1L-${i}.json"
  cutsLocation="${baseDir}/VR1L${i}Cuts"

  outputNMinus1="n-1/VR1L-${i}"
  python do_n-1_cuts.py ${files[*]} --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json -f

  python optimize.py cut ${files[*]} --supercuts $supercutsLocation -o $cutsLocation --numpy -v -b

  for lumi in 2
  do

    significancesLocation="${baseDir}/VR1L${i}Significances_${lumi}"

    python optimize.py optimize --signal 37* --bkgd 410000.json 407012.json --searchDirectory $cutsLocation -b --o $significancesLocation --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi $lumi

    outputHashLocation="${baseDir}/outputHash_VR1L${i}_${lumi}"

    python write_all_optimal_cuts.py --supercuts $supercutsLocation --significances $significancesLocation -o $outputHashLocation

    outputFilePlots="VR1L${i}_${lumi}"
    python graph-grid.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --cutdir $cutsLocation
    python graph-cuts.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --supercuts $supercutsLocation --hashdir $outputHashLocation
  done
done
