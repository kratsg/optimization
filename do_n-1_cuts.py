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

parser.add_argument('-f', '--force', action='store_true', dest='overwrite', help='Overwrite the directory if it exists')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

import json
from itertools import combinations
import operator
import optimize
import ROOT
import sys
from collections import defaultdict

from rootpy.io import root_open
from rootpy.plotting import Hist
from rootpy.plotting import set_style
from rootpy.tree import Tree, TreeChain

supercuts = json.load(file(args.supercuts, 'r'))
boundaries = json.load(file(args.boundaries, 'r'))

for fname in args.files:
  # first open file
  print("Opening {0}".format(fname))
  out_file = root_open(fname, "UPDATE")

  '''
    Given a file and a path to a directory to create, check if parent exists
    and then try to create if it doesn't. Then cd() into it, and create the
    base directory needed. If it exists, remove if required, then create and cd.
  '''

  parent_dir = os.path.dirname(args.output)
  if getattr(out_file, parent_dir, None) is None:
    print("\tMaking {0}".format(parent_dir))
    out_file.mkdir(parent_dir, recurse=True)

  # now that we know parent directory exists...
  parent_dir = getattr(out_file, parent_dir)
  # get the base directory to create
  base_dir = os.path.basename(args.output)
  # if it exists and user wants to overwrite, do so
  out_file.rmdir(base_dir)
  if getattr(parent_dir, base_dir, None) and args.overwrite:
    print("\tRemoving {0}".format(base_dir))
    parent_dir.rmdir(base_dir)
  try:
    # this will crash here if the user doesn't choose to overwrite directory that exists
    print("\tMaking {0}".format(base_dir))
    parent_dir.mkdir(base_dir)
  except ValueError:
    print("\t\tThis exists. Try re-running with -f, --force to overwrite the existing directory or specify a different output directory")
    sys.exit(1)

  # guess we're all ok, so cd and continue
  print("\tCd'ing into {0}".format(args.output))
  out_file.cd(args.output)

  differences = []
  #c = ROOT.TCanvas("canvas", "canvas", 500, 500)
  for subercuts in combinations(supercuts, len(supercuts)-1):
    # hold the differences and create a text file with them later for reference
    # use integers to denote them
    differences.append([x for x in supercuts if x not in subercuts][0])

    # get the tree
    tree = getattr(out_file, args.tree_name)

    # get the selection we apply to draw it
    selection = optimize.cuts_to_selection(subercuts)
    # get the branch we need to draw
    selection_string = differences[-1]['selections']

    print("\tLooking at selection: {0}".format(selection_string))
    branchesSpecified = set(optimize.selection_to_branches(selection_string, tree))
    # get actual list of branches in the file
    availableBranches = optimize.tree_get_branches(tree, args.eventWeightBranch)
    # remove anything that doesn't exist
    branchesToUse = [branch for branch in branchesSpecified if branch in availableBranches]

    # more than one branch, we skip and move to the next
    if len(branchesToUse) != 1:
      print("\t\tWarning: selection has multiple branches.")
      del differences[-1]
      continue

    branchToDraw = branchesToUse[0]
    print("\t\tDrawing {0}".format(branchToDraw))

    h = Hist(boundaries[branchToDraw][2], boundaries[branchToDraw][0], boundaries[branchToDraw][1], name=branchToDraw)
    # draw with selection and branch
    tree.Draw(branchToDraw, '{0:s}*{1:s}'.format(args.eventWeightBranch, selection), hist = h)

    # write to file
    print("\t\tWriting to file")
    h.write()

    # now that we have a sub-supercuts, let's actually do_cuts
    subercutsFile = os.path.join(args.output, '{0}.json'.format(branchToDraw))
    with open(subercutsFile, 'w+') as f:
      f.write(json.dumps(subercuts, sort_keys=True, indent=4))

  print("\tClosing file")
  out_file.close()
