import json
import glob
import os
import re
import copy

# write scalefactor in ifb
scaleFactor = 2

# edit with the path to the files you're looking at, so we can figure out did to group mapping
pathToFiles = r'/Users/kratsg/Dropbox/TheAccountant_dataFiles/TA01_MBJ13V4'

# this holds a list of various subset of counts
count_types = ['raw', 'weighted', 'scaled']

# this holds a structure of a group with the control region counts and signal region counts
groups = {}

# get the did to group mapping
files = glob.glob(os.path.join(pathToFiles, "*_*L/fetch/data-optimizationTree/*.root"))
p = re.compile(os.path.join(pathToFiles, r'(.*?)_\dL/fetch/data-optimizationTree/.*(\d{6}).*root'))
did_to_group = {}

for f in files:
  group, did = p.search(f).groups()
  if 'ttbar' in group: group = 'ttbar'
  did_to_group[did] = group

for regionID in range(1, 5):
  for fname in glob.glob("CR/CR{0:d}Cuts/*.json".format(regionID))+glob.glob("SR/SR{0:d}Cuts/*.json".format(regionID)):
    did = os.path.basename(fname).split('.')[0]

    # figure out if we're using SR or CR
    region='CR'
    if 'SR' in os.path.basename(os.path.dirname(fname)): region='SR'

    with open(fname) as f:
      data = json.load(f)
      # add in the group
      group = did_to_group[did]
      # no signal allowed
      if group == 'Gtt': continue
      # if we haven't added the group yet, set up defaults
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
        if count_type == 'scaled': sf = scaleFactor*1000
        groups[did_to_group[did]][region][regionID][count_type] += data[count_type]*sf

for index, typeBkgd in zip(count_types, ['raw', 'weighted', 'scaled ({0:0.4f}ifb)'.format(scaleFactor)]):
  sumValues = [0]*8
  print("{0: ^150s}".format(typeBkgd))
  printStr = "{{0:12}}{0:s}1{0:s}2{0:s}3{0:s}4{1:s}1{1:s}2{1:s}3{1:s}4".format("\t{1:>9}", "\t{2:>9}")
  print(printStr.format("GROUP", "SR", "CR"))
  for group in sorted(groups):
    values = [group] + [groups[group][region][i][index] for region in ['SR', 'CR'] for i in range(1,5)]
    valueStr = "{{0:12}}\t{{1:{0:s}}}\t{{2:{0:s}}}\t{{3:{0:s}}}\t{{4:{0:s}}}\t{{5:{0:s}}}\t{{6:{0:s}}}\t{{7:{0:s}}}\t{{8:{0:s}}}".format("10.4f")
    print(valueStr.format(*values))
    sumValues = [sum(x) for x in zip(sumValues, values[1:])]
  print("\t"+("-"*100))
  sumValues = ["total"] + sumValues
  print(valueStr.format(*sumValues))
  print("="*100)
