# first, run to produce baseline selections

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_baseline.json -o baselineCuts --numpy -v -b

# njet was maxed at 10, but this overlaps with another group. How bad is it if we bump this down to a max of 7?

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_njetMax.json -o njetMaxCuts --numpy -v -b


# next, we want to compute significances for it all
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=baselineCuts -b --o=baselineSignificances --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1

python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=njetMaxCuts -b --o=njetMaxSignificances --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1

# next, find all optimal hashes by running
python write_all_optimal_cuts.py
# after editing the top few lines for appropriate directories

# finally, make plots
python graph-grid.py --lumi 1 --outfile baseline --sigdir baselineSignificances --cutdir baselineCuts

python graph-grid.py --lumi 1 --outfile njetMax --sigdir njetMaxSignificances --cutdir njetMaxCuts
