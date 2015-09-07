# first, run to produce baseline selections

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_baseline.json -o baselineCuts --numpy -v -b
