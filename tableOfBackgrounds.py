import json
import glob
import os
import re
import copy
import numpy

import argparse
import subprocess
import os
from optimize import utils

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: G. Stark. v.{0}'.format(__version__), formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('--regions', type=str, metavar='<regions.json>', required=True, help='JSON file defining the regions and paths to the cuts to look at')
parser.add_argument('--did_to_group', type=str, metavar='did_to_group.json', required=True, help='JSON dictionary containing a mapping from a DID to a group name')
parser.add_argument('--lumi', required=False, type=int, dest='lumi', metavar='<L>', help='luminosity to use in ifb', default=1)
parser.add_argument('--hide-raw', required=False, action='store_true', help='Hide raw counts')
parser.add_argument('--hide-weighted', required=False, action='store_true', help='Hide weighted counts')
parser.add_argument('--hide-scaled', required=False, action='store_true', help='Hide scaled counts')
parser.add_argument('--skip-groups', required=False, nargs='+', help='Hide specific groups from output', default=['Gbb','Gtt'])
parser.add_argument('--include-dids', required=False, nargs='+', help='Include the following DIDs in background calculation', default=[])
parser.add_argument('--hide-invalid-dids', required=False, action='store_true', help='Suppress statements about invalid DIDs')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

# this holds a list of various subset of counts
count_types = ['raw', 'weighted', 'scaled']
if args.hide_raw: count_types.remove('raw')
if args.hide_weighted: count_types.remove('weighted')
if args.hide_scaled: count_types.remove('scaled')

# this holds a structure of a group with the region counts
groups = {}

# first load regions file and did-to-group mapping
regions = json.load(file(args.regions))
did_to_group = json.load(file(args.did_to_group))

nullregion = dict((count_type, 0) for count_type in count_types)
nullgroup = dict((region['name'], copy.deepcopy(nullregion)) for region in regions)

for region in regions:
  for fpattern in region['cuts']:
    for fname in glob.glob(fpattern):
      did = utils.get_did(fname)
      try:
        int(did)
      except ValueError:
        if not args.hide_invalid_dids:
          print 'No valid DID found. Skipping {0}'.format(fname)
        continue #skip because it's probably a bad thing to use
      if did not in args.include_dids: continue

      with open(fname) as f:
        data = json.load(f)
        # add in the group
        group = did_to_group[did]
        # no signal allowed
        if group in args.skip_groups: continue
        # we haven't done this group yet
        if group not in groups: groups[group] = copy.deepcopy(nullgroup)

        # we just need the subset which is often first item (look at an example json)
        data = data[data.keys()[0]]
        for count_type in count_types:
          sf = 1
          if count_type == 'scaled': sf = args.lumi*1000
          groups[group][region['name']][count_type] += data[count_type]*sf

def getValues(group, groups, count_type):
  return [group] + [groups[group][region['name']][count_type] for region in regions]

# make a table for each count_type we look at
for count_type in count_types:
  # figure out the maximum column width
  max_column_width = max(max(len(region['name']) for region in regions), 7)+4

  # specify whether we look at raw, weighted, or scaled (table caption) at the top
  header_label = count_type+(' ({0:0.2f}ifb)'.format(args.lumi) if (count_type == 'scaled') else '')
  print(" "*max_column_width+"{0: ^{1}s}".format(header_label, max_column_width*len(regions)))

  # define the table header row
  printStr = "{0:<{1}s}".format("GROUP", max_column_width)
  printStr += "".join("{0:>{1}s}".format(region['name'], max_column_width) for region in regions)
  print(printStr)

  # this specifies the format for rows of actual data/counts
  valueStr = "{{0:<{0}s}}".format(max_column_width)
  valueStr += "".join("{{{0}:{1}.2f}}".format(i+1, max_column_width) for i in range(len(regions)))

  # initialize a row of zeros to keep track of sums
  sumValues = [0]*len(regions)
  for group in sorted(groups):
    values = getValues(group, groups, count_type)
    print(valueStr.format(*values))
    sumValues = [sum(x) for x in zip(sumValues, values[1:])]
  print(" "*max_column_width+"-"*max_column_width*len(regions))
  sumValues = ["total"] + sumValues
  print(valueStr.format(*sumValues))
  # add ttbar fraction
  ttbarFrac = getValues('ttbar', groups, count_type)
  ttbarFrac[0] = '%ttbar'
  for i in range(1, len(ttbarFrac)):
    ttbarFrac[i] = numpy.float64(ttbarFrac[i])/sumValues[i]
  print(valueStr.format(*ttbarFrac))
  print(" "*max_column_width+"="*max_column_width*len(regions))

