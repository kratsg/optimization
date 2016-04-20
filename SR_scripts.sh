#!/bin/bash

files=()
#for sample in "Gtt" "ttbarInc" "ttbarExc" "Wsherpa" "Zsherpa" "dijet" "data" "singletop" "topEW" "diboson"
#do
    #files+=($(find ./TA02_MBJ13V4-6/"${sample}"_0L/fetch/data-optimizationTree/*.root -print0 | xargs -0))
#done
files+=($(find /home/mleblanc/Optimization/input/hf_nom_v7/*.root -print0 | xargs -0))

baseDir="SR"
rm -rf $baseDir
mkdir -p $baseDir

for i in 1 2 3 4
do
  supercutsLocation="supercuts2k16/SR-${i}.json"
  cutsLocation="/home/mleblanc/Optimization/SR${i}Cuts/"

  outputNMinus1="nMinus1/SR${i}"
  python do_n-1_cuts.py ${files[*]} --supercuts $supercutsLocation --output $outputNMinus1 --boundaries boundaries.json --tree nominal -f --eventWeight "weight_mc*weight_btag*weight_elec*weight_muon*weight_pu"

  python optimize.py cut ${files[*]} --supercuts $supercutsLocation -o $cutsLocation --tree nominal --numpy -v -b --eventWeight "weight_mc*weight_btag*weight_elec*weight_muon*weight_pu"

  for lumi in 10
  do
    significancesLocation="${baseDir}/SR${i}Significances_${lumi}"
    
    python optimize.py optimize --signal 3701* --bkgd 31* 36* 34* 41* 407* --searchDirectory $cutsLocation -b --o $significancesLocation --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi $lumi

    outputHashLocation="${baseDir}/outputHash_SR${i}_${lumi}"

    python write_all_optimal_cuts.py --supercuts $supercutsLocation --significances $significancesLocation -o $outputHashLocation

    outputFilePlots="SR${i}_${lumi}"
    python graph-grid.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --cutdir $cutsLocation
    python graph-cuts.py --lumi $lumi --outfile $outputFilePlots --sigdir $significancesLocation --supercuts $supercutsLocation --hashdir $outputHashLocation
  done
done

for lumi in 10
do
  python find_optimal_signal_region.py --lumi $lumi --basedir $baseDir
done
