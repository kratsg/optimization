#!/bin/bash

# 0L
python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/*_0L/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_0L --numpy -b
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=cuts_0L -b --o=significances_0L --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=2
python graph-grid.py --lumi 5 --outfile "output_0L.pdf" --sigdir "significances_0L"

# 1L
python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/*_1L/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_1L --numpy -b
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=cuts_1L -b --o=significances_1L --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=2
python graph-grid.py --lumi 5 --outfile "output_1L.pdf" --sigdir "significances_1L"
