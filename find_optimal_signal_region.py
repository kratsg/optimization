import argparse
import subprocess
import os

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: A. Cukierman, G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('--lumi', required=False, type=int, dest='lumi', metavar='<L>', help='luminosity to use', default=1)
parser.add_argument('-o', '--output', required=False, type=str, dest='output', metavar='', help='basename to use for output filename', default='output')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

import ROOT
import csv
import glob
import re
import json
from collections import defaultdict

# given a DID, we get the mass points, translates to a box on the graph for us
with open('mass_windows.txt', 'r') as f:
  reader = csv.reader(f, delimiter='\t')
  m = list(reader)
mdict = {l[0]: [l[1],l[2],l[3]] for l in m}
del m

# start up a dictionary to hold all information
significances = defaultdict(lambda: {1: 0, 2: 0, 3: 0, 4: 0})

p_did = re.compile('s(\d+)\.b([0-9\-]+)\.json')

# for each signal region, build up the significance value
for i in range(1,5):
  files = glob.glob("SR{0:d}Significances_{1:d}/s*.b*.json".format(i, args.lumi))
  for filename in files:
    with open(filename, 'r') as f:
      data = json.load(f)
    did = p_did.search(filename).group(1)
    significances[did][i] = data[0]['significance_scaled']

import operator
winners = {1: 0, 2: 0, 3: 0, 4: 0}
for did, vals in significances.iteritems():
  winners[max(vals.iteritems(), key=operator.itemgetter(1))[0]] += 1

print winners
