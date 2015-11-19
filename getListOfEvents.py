from optimize import logger, get_ttree, selection_to_branches, tree_get_branches, cuts_to_selection
import json
import root_numpy as rnp
import glob
import itertools
import numexpr as ne
import numpy as np
import os
from collections import defaultdict

skipRegions = ["old", "SR", "VR0"]

regions = sorted([region for region in glob.glob('supercuts/*-*.json') if all([skipRegion not in region for skipRegion in skipRegions])], key=lambda x: int(x.split('.')[0].split('-')[1]))
eventNumbers = defaultdict(list)

tree_name = 'oTree'
eventWeightBranch = 'event_number'
files = glob.glob("TA02_MBJ13V4-6/data_0L/fetch/data-optimizationTree/*.root")

for region in regions:
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
        eventNumbers[event_number].append(region)
    #    print "\t", event_number

overlapsByColumn = [0]*(len(regions)/2)

print "{0:s}\t\t{1:s}\t| {2:s}".format("Event #", "\t".join(map(lambda x: os.path.basename(x).split('.')[0], regions)), "# Overlaps")
print "-"*80
for event_number, in_regions in eventNumbers.iteritems():
    overlaps = [bool(region in in_regions) for region in regions]
    numOverlapsInRow = 0
    for i in range(0, len(overlaps), 2):
        numOverlapsInRow += overlaps[i]&overlaps[i+1]
        overlapsByColumn[i/2] += overlaps[i]&overlaps[i+1]
    print "{0:d}\t{1:s}\t| {2:>10d}".format(event_number, "\t".join(("x" if overlap else "") for overlap in overlaps), numOverlapsInRow)

print "-"*80
print "{0:s}\t{1:s}".format("{0:d} events".format(len(eventNumbers)), "\t\t".join(map(str, overlapsByColumn)))
