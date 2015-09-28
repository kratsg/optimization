import argparse
import subprocess
import os

'''
TO DO:
  - automatically grab the parsers from optimize.py instead of copying them over...
'''

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('files', type=str, nargs='+', metavar='<file.root>', help='ROOT files containing the optimization ntuples')
parser.add_argument('--supercuts', required=True, type=str, dest='supercuts', metavar='<file.json>', help='json dict of supercuts to generate optimization cuts to apply')
parser.add_argument('--output', required=False, type=str, dest='output', metavar='', help='name of directory to keep all generated outputs', default='n-1')

parser.add_argument('--tree', type=str, required=False, dest='tree_name', metavar='<tree name>', help='name of the tree containing the ntuples', default='oTree')
parser.add_argument('--eventWeight', type=str, required=False, dest='eventWeightBranch', metavar='<branch name>', help='name of event weight branch in the ntuples. It must exist.', default='event_weight')
parser.add_argument('--boundaries', type=str, required=False, dest='boundaries', metavar='<file.json>', help='name of json file containing boundary definitions', default='boundaries.json')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

import json
from itertools import combinations
import operator
import optimize
import ROOT
from collections import defaultdict

from rootpy.io import root_open
from rootpy.plotting import Hist
from rootpy.plotting import set_style
from rootpy.tree import Tree, TreeChain

supercuts = json.load(file(args.supercuts, 'r'))
boundaries = json.load(file(args.boundaries, 'r'))

# first step is to group by the sample DID
dids = defaultdict(list)
for fname in args.files:
  dids[optimize.get_did(fname)].append(fname)

# loop by did and file
for did, files in dids.iteritems():
  # first open file
  out_file = root_open(os.path.join(args.output, "n-1.{0}.root".format(did)), "NEW")
  out_file.mkdir('all')
  out_file.cd('all')

  differences = []
  #c = ROOT.TCanvas("canvas", "canvas", 500, 500)
  for subercuts in combinations(supercuts, len(supercuts)-1):
    # hold the differences and create a text file with them later for reference
    # use integers to denote them
    differences.append([x for x in supercuts if x not in subercuts][0])

    # get the tree
    tree = TreeChain(args.tree_name, files)

    # get the selection we apply to draw it
    selection = optimize.cuts_to_selection(subercuts)
    # get the branch we need to draw
    selection_string = differences[-1]['selections']

    branchesSpecified = set(optimize.selection_to_branches(selection_string, tree))
    # get actual list of branches in the file
    availableBranches = optimize.tree_get_branches(tree, args.eventWeightBranch)
    # remove anything that doesn't exist
    branchesToUse = [branch for branch in branchesSpecified if branch in availableBranches]

    # more than one branch, we skip and move to the next
    if len(branchesToUse) != 1:
      print("\tWarning: selection has multiple branches.\n\tSelection: {0}".format(selection_string))
      del differences[-1]
      continue

    branchToDraw = branchesToUse[0]
    print("Drawing {0}".format(branchToDraw))

    h = Hist(100, boundaries[branchToDraw][0], boundaries[branchToDraw][1], name=branchToDraw)
    # draw with selection and branch
    tree.Draw(branchToDraw, '{0:s}*{1:s}'.format(args.eventWeightBranch, selection), hist = h)

    # write to file
    h.write()

    # now that we have a sub-supercuts, let's actually do_cuts
    subercutsFile = os.path.join(args.output, '{0}.json'.format(branchToDraw))
    with open(subercutsFile, 'w+') as f:
      f.write(json.dumps(subercuts, sort_keys=True, indent=4))

  out_file.close()
