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
parser.add_argument('--weightsFile', type=str, required=False, dest='weightsFile', metavar='<weights file>', help='yml file containing weights by DID', default='weights.yml')
parser.add_argument('--output', required=False, type=str, dest='output', metavar='', help='name of directory to keep all generated outputs', default='n-1')

parser.add_argument('--tree', type=str, required=False, dest='tree_name', metavar='<tree name>', help='name of the tree containing the ntuples', default='oTree')
parser.add_argument('--eventWeight', type=str, required=False, dest='eventWeightBranch', metavar='<branch name>', help='name of event weight branch in the ntuples. It must exist.', default='event_weight')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

import json
from itertools import combinations
import operator

supercuts = json.load(file(args.supercuts, 'r'))

differences = []
level = 0
for subercuts in combinations(supercuts, len(supercuts)-1):
  level += 1
  # hold the differences and create a text file with them later for reference
  # use integers to denote them
  differences.append([x for x in supercuts if x not in subercuts][0])
  # now that we have a sub-supercuts, let's actually do_cuts
  subercutsFile = os.path.join(args.output, '{0:d}.json'.format(level))
  with open(subercutsFile, 'w+') as f:
    f.write(json.dumps(subercuts, sort_keys=True, indent=4))

  # build arguments for do_cuts
  do_cuts_call = ['./optimize.py', 'cut'] + args.files + ['--supercuts', subercutsFile] + ['-o', os.path.join(args.output, str(level))] + ['--numpy', '-v', '-b']
  subprocess.call(do_cuts_call)
