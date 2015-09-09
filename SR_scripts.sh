#!/bin/bash
for i in 1 2 3 4
do
  supercutsLocation = "supercuts/SR-${i}.json"
  cutsLocation = "SR${i}Cuts"

  python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root --supercuts=${supercutsLocation} -o ${cutsLocation} --numpy -v -b

  for lumi in 1 2 4 10
  do
    significancesLocation = "SR${i}Significances_${lumi}"
    python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=${cutsLocation} -b --o=${significancesLocation} --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=${lumi}
  done
done
