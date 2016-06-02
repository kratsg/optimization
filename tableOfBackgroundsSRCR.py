import json
import glob
import os
import re
import copy
import numpy

import argparse
import subprocess
import os

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: G. Stark. v.{0}'.format(__version__), formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('files', type=str, nargs='+', metavar='<file.root>', help='ROOT files containing the optimization ntuples')
parser.add_argument('--lumi', required=False, type=int, dest='lumi', metavar='<L>', help='luminosity to use in ifb', default=1)
parser.add_argument('--hide-raw', required=False, action='store_true', help='Hide raw counts')
parser.add_argument('--hide-weighted', required=False, action='store_true', help='Hide weighted counts')
parser.add_argument('--hide-scaled', required=False, action='store_true', help='Hide scaled counts')
parser.add_argument('--skip-groups', required=False, nargs='+', help='Hide specific groups from output', default=['Gbb','Gtt'])
parser.add_argument('--include-dids', required=False, nargs='+', help='Include the following DIDs in background calculation', default=[])

# parse the arguments, throw errors if missing any
args = parser.parse_args()

# this holds a list of various subset of counts
count_types = ['raw', 'weighted', 'scaled']
if args.hide_raw: count_types.remove('raw')
if args.hide_weighted: count_types.remove('weighted')
if args.hide_scaled: count_types.remove('scaled')

# this holds a structure of a group with the control region counts and signal region counts
groups = {}

# get the did to group mapping
p = re.compile(r'.*(\d{6})\.([^.]*?)\..*')
did_to_group = {}

for f in args.files:
  try:
    did, group = p.search(os.path.basename(f)).groups()
    did_to_group[did] = group
  except AttributeError:
    print 'Skipping {0}'.format(f)
    args.files.remove(f)
    continue

for regionID in range(1, 5):
  for fname in glob.glob("CR/CR{0:d}Cuts/*.json".format(regionID))+glob.glob("SR/SR{0:d}Cuts/*.json".format(regionID)):
    did = os.path.basename(fname).split('.')[0]
    try:
      int(did)
    except ValueError:
      continue #skip because it's probably a bad thing to use
    if did not in args.include_dids: continue

    # figure out if we're using SR or CR
    region='CR'
    if 'SR' in os.path.basename(os.path.dirname(fname)): region='SR'

    with open(fname) as f:
      data = json.load(f)
      # add in the group
      group = did_to_group[did]
      # no signal allowed
      if group in args.skip_groups: continue
      if group not in groups:
        nullregion = dict((count_type, 0) for count_type in count_types)
        nulldict = {1: copy.deepcopy(nullregion),
                    2: copy.deepcopy(nullregion),
                    3: copy.deepcopy(nullregion),
                    4: copy.deepcopy(nullregion)}
        groups[group] = {'SR': copy.deepcopy(nulldict), 'CR': copy.deepcopy(nulldict)}

      # we just need the subset which is often first item (look at an example json)
      data = data[data.keys()[0]]
      for count_type in count_types:
        sf = 1
        # scale by 2ifb
        if count_type == 'scaled': sf = args.lumi*1000
        groups[did_to_group[did]][region][regionID][count_type] += data[count_type]*sf

def getValues(group, groups):
  return [group] + [groups[group][region][i][index] for region in ['SR', 'CR'] for i in range(1,5)]

for index, typeBkgd in zip(count_types, ['raw', 'weighted', 'scaled ({0:0.4f}ifb)'.format(args.lumi)]):
  sumValues = [0]*8
  print("{0: ^150s}".format(typeBkgd))
  printStr = "{{0:12}}{0:s}1{0:s}2{0:s}3{0:s}4{1:s}1{1:s}2{1:s}3{1:s}4".format("\t{1:>9}", "\t{2:>9}")
  print(printStr.format("GROUP", "SR", "CR"))
  valueStr = "{{0:12}}\t{{1:{0:s}}}\t{{2:{0:s}}}\t{{3:{0:s}}}\t{{4:{0:s}}}\t{{5:{0:s}}}\t{{6:{0:s}}}\t{{7:{0:s}}}\t{{8:{0:s}}}".format("10.4f")
  for group in sorted(groups):
    values = getValues(group, groups)
    print(valueStr.format(*values))
    sumValues = [sum(x) for x in zip(sumValues, values[1:])]
  print("\t"+("-"*100))
  sumValues = ["total"] + sumValues
  print(valueStr.format(*sumValues))
  # add ttbar fraction
  ttbarFrac = getValues('ttbar', groups)
  ttbarFrac[0] = '%ttbar'
  for i in range(1, len(ttbarFrac)):
    ttbarFrac[i] = numpy.float64(ttbarFrac[i])/sumValues[i]
  print(valueStr.format(*ttbarFrac))
  print("="*100)
