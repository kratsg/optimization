python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root --supercuts=supercuts_baseline.json -o baselineCuts --numpy -v -b

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root --supercuts=supercuts_massScan.json -o massScanCuts --numpy -v -b

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root --supercuts=supercuts_no_mTb.json -o nomTbCuts --numpy -v -b

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root --supercuts=supercuts_fixedMassScan.json -o fixedMassScanCuts --numpy -v -b

python optimize.py cut ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/Gtt_0L_b/fetch/data-optimizationTree/*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*410000*r6765_r6282*.root ~/Dropbox/TheAccountant_dataFiles/TA07_MBJ10V1/ttbar*_0L_b/fetch/data-optimizationTree/*407012*r6765_r6282*p2411*.root --supercuts=supercuts_noTagger.json -o noTaggerCuts --numpy -v -b

# next, we want to compute significances for it all
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=baselineCuts -b --o=baselineSignificances_1 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=baselineCuts -b --o=baselineSignificances_2 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=2
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=baselineCuts -b --o=baselineSignificances_4 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=4
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=baselineCuts -b --o=baselineSignificances_10 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=10

python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=massScanCuts -b --o=massScanSignificances_1 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=massScanCuts -b --o=massScanSignificances_2 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=2
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=massScanCuts -b --o=massScanSignificances_4 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=4
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=massScanCuts -b --o=massScanSignificances_10 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=10

python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=nomTbCuts -b --o=nomTbSignificances_1 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=nomTbCuts -b --o=nomTbSignificances_2 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=2
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=nomTbCuts -b --o=nomTbSignificances_4 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=4
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=nomTbCuts -b --o=nomTbSignificances_10 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=10

python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=fixedMassScanCuts -b --o=fixedMassScanSignificances_1 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=fixedMassScanCuts -b --o=fixedMassScanSignificances_2 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=2
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=fixedMassScanCuts -b --o=fixedMassScanSignificances_4 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=4
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=fixedMassScanCuts -b --o=fixedMassScanSignificances_10 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=10

python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=noTaggerCuts -b --o=noTaggerSignificances_1 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=1
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=noTaggerCuts -b --o=noTaggerSignificances_2 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=2
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=noTaggerCuts -b --o=noTaggerSignificances_4 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=4
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=noTaggerCuts -b --o=noTaggerSignificances_10 --bkgdUncertainty=0.3 --bkgdStatUncertainty=0.3 --insignificance=0.5 --lumi=10

# next, find all optimal hashes by running
python write_all_optimal_cuts.py
# after editing the top few lines for appropriate directories

# finally, make plots
python graph-grid.py --lumi 1 --outfile baseline1 --sigdir baselineSignificances_1 --cutdir baselineCuts
python graph-grid.py --lumi 2 --outfile baseline2 --sigdir baselineSignificances_2 --cutdir baselineCuts
python graph-grid.py --lumi 4 --outfile baseline4 --sigdir baselineSignificances_4 --cutdir baselineCuts
python graph-grid.py --lumi 10 --outfile baseline10 --sigdir baselineSignificances_10 --cutdir baselineCuts

python graph-grid.py --lumi 1 --outfile massScan1 --sigdir massScanSignificances_1 --cutdir massScanCuts
python graph-grid.py --lumi 2 --outfile massScan2 --sigdir massScanSignificances_2 --cutdir massScanCuts
python graph-grid.py --lumi 4 --outfile massScan4 --sigdir massScanSignificances_4 --cutdir massScanCuts
python graph-grid.py --lumi 10 --outfile massScan10 --sigdir massScanSignificances_10 --cutdir massScanCuts

python graph-grid.py --lumi 1 --outfile nomTb1 --sigdir nomTbSignificances_1 --cutdir nomTbCuts
python graph-grid.py --lumi 2 --outfile nomTb2 --sigdir nomTbSignificances_2 --cutdir nomTbCuts
python graph-grid.py --lumi 4 --outfile nomTb4 --sigdir nomTbSignificances_4 --cutdir nomTbCuts
python graph-grid.py --lumi 10 --outfile nomTb10 --sigdir nomTbSignificances_10 --cutdir nomTbCuts

python graph-grid.py --lumi 1 --outfile fixedMassScan1 --sigdir fixedMassScanSignificances_1 --cutdir fixedMassScanCuts
python graph-grid.py --lumi 2 --outfile fixedMassScan2 --sigdir fixedMassScanSignificances_2 --cutdir fixedMassScanCuts
python graph-grid.py --lumi 4 --outfile fixedMassScan4 --sigdir fixedMassScanSignificances_4 --cutdir fixedMassScanCuts
python graph-grid.py --lumi 10 --outfile fixedMassScan10 --sigdir fixedMassScanSignificances_10 --cutdir fixedMassScanCuts

python graph-grid.py --lumi 1 --outfile noTagger1 --sigdir noTaggerSignificances_1 --cutdir noTaggerCuts
python graph-grid.py --lumi 2 --outfile noTagger2 --sigdir noTaggerSignificances_2 --cutdir noTaggerCuts
python graph-grid.py --lumi 4 --outfile noTagger4 --sigdir noTaggerSignificances_4 --cutdir noTaggerCuts
python graph-grid.py --lumi 10 --outfile noTagger10 --sigdir noTaggerSignificances_10 --cutdir noTaggerCuts

python graph-cuts.py --lumi 1 --outfile baseline1 --sigdir baselineSignificances_1 --supercuts supercuts_baseline.json --hashdir outputHash_baseline_1
python graph-cuts.py --lumi 2 --outfile baseline2 --sigdir baselineSignificances_2 --supercuts supercuts_baseline.json --hashdir outputHash_baseline_2
python graph-cuts.py --lumi 4 --outfile baseline4 --sigdir baselineSignificances_4 --supercuts supercuts_baseline.json --hashdir outputHash_baseline_4
python graph-cuts.py --lumi 10 --outfile baseline10 --sigdir baselineSignificances_10 --supercuts supercuts_baseline.json --hashdir outputHash_baseline_10

python graph-cuts.py --lumi 1 --outfile massScan1 --sigdir massScanSignificances_1 --supercuts supercuts_massScan.json --hashdir outputHash_massScan_1
python graph-cuts.py --lumi 2 --outfile massScan2 --sigdir massScanSignificances_2 --supercuts supercuts_massScan.json --hashdir outputHash_massScan_2
python graph-cuts.py --lumi 4 --outfile massScan4 --sigdir massScanSignificances_4 --supercuts supercuts_massScan.json --hashdir outputHash_massScan_4
python graph-cuts.py --lumi 10 --outfile massScan10 --sigdir massScanSignificances_10 --supercuts supercuts_massScan.json --hashdir outputHash_massScan_10

python graph-cuts.py --lumi 1 --outfile nomTb1 --sigdir nomTbSignificances_1 --supercuts supercuts_no_mTb.json --hashdir outputHash_nomTb_1
python graph-cuts.py --lumi 2 --outfile nomTb2 --sigdir nomTbSignificances_2 --supercuts supercuts_no_mTb.json --hashdir outputHash_nomTb_2
python graph-cuts.py --lumi 4 --outfile nomTb4 --sigdir nomTbSignificances_4 --supercuts supercuts_no_mTb.json --hashdir outputHash_nomTb_4
python graph-cuts.py --lumi 10 --outfile nomTb10 --sigdir nomTbSignificances_10 --supercuts supercuts_no_mTb.json --hashdir outputHash_nomTb_10

python graph-cuts.py --lumi 1 --outfile fixedMassScan1 --sigdir fixedMassScanSignificances_1 --supercuts supercuts_fixedMassScan.json --hashdir outputHash_fixedMassScan_1
python graph-cuts.py --lumi 2 --outfile fixedMassScan2 --sigdir fixedMassScanSignificances_2 --supercuts supercuts_fixedMassScan.json --hashdir outputHash_fixedMassScan_2
python graph-cuts.py --lumi 4 --outfile fixedMassScan4 --sigdir fixedMassScanSignificances_4 --supercuts supercuts_fixedMassScan.json --hashdir outputHash_fixedMassScan_4
python graph-cuts.py --lumi 10 --outfile fixedMassScan10 --sigdir fixedMassScanSignificances_10 --supercuts supercuts_fixedMassScan.json --hashdir outputHash_fixedMassScan_10

python graph-cuts.py --lumi 1 --outfile noTagger1 --sigdir noTaggerSignificances_1 --supercuts supercuts_noTagger.json --hashdir outputHash_noTagger_1
python graph-cuts.py --lumi 2 --outfile noTagger2 --sigdir noTaggerSignificances_2 --supercuts supercuts_noTagger.json --hashdir outputHash_noTagger_2
python graph-cuts.py --lumi 4 --outfile noTagger4 --sigdir noTaggerSignificances_4 --supercuts supercuts_noTagger.json --hashdir outputHash_noTagger_4
python graph-cuts.py --lumi 10 --outfile noTagger10 --sigdir noTaggerSignificances_10 --supercuts supercuts_noTagger.json --hashdir outputHash_noTagger_10

