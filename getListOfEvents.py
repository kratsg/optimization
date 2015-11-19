from optimize import logger, get_ttree, selection_to_branches, tree_get_branches, cuts_to_selection
import json
import root_numpy as rnp
import glob
import itertools
import numexpr as ne
import numpy as np
import os

regions = glob.glob('supercuts/*-*.json')
tree_name = 'oTree'
eventWeightBranch = 'event_number'
files = glob.glob("TA02_MBJ13V4-6/data_0L/fetch/data-optimizationTree/*.root")

for region in regions:
    if "old" in region: continue
    print os.path.basename(region)
    supercuts = json.load(file(region))

    tree = get_ttree(tree_name, files, eventWeightBranch)
    branchesSpecified = list(set(itertools.chain.from_iterable(selection_to_branches(supercut['selections'], tree) for supercut in supercuts)))
    eventWeightBranchesSpecified = list(set(selection_to_branches(eventWeightBranch, tree)))

    # get actual list of branches in the file
    availableBranches = tree_get_branches(tree, eventWeightBranchesSpecified)

    # remove anything that doesn't exist
    branchesToUse = [branch for branch in branchesSpecified if branch in availableBranches]
    branchesSkipped = list(set(branchesSpecified) - set(branchesToUse))
    if branchesSkipped:
        logger.info("The following branches have been skipped...")
    for branch in branchesSkipped:
        logger.info("\t{0:s}".format(branch))
    tree = rnp.tree2array(tree, branches=eventWeightBranchesSpecified+branchesToUse)

    entireSelection = '{0:s}*{1:s}'.format(eventWeightBranch, cuts_to_selection(supercuts))

    result = ne.evaluate(entireSelection, local_dict = tree)

    for event_number in result[np.where(result!=0)]:
        print "\t", event_number
