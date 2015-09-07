# first, run to produce baseline selections

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_baseline.json -o baselineCuts --numpy -v -b

# njet was maxed at 10, but this overlaps with another group. How bad is it if we bump this down to a max of 7?

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_njetMax.json -o njetMaxCuts --numpy -v -b

