import json
import glob
import os
import re
import copy
import numpy

# write scalefactor in ifb
scaleFactor = 10

# edit with the path to the files you're looking at, so we can figure out did to group mapping
pathToFiles = r'/home/mleblanc/Optimization/input/hf_nom_v7/'
#pathToFiles = r'/home/mleblanc/Optimization/input/temp/'

# this holds a list of various subset of counts
count_types = ['raw', 'weighted', 'scaled']

# this holds a structure of a group with the control region counts and signal region counts
# groups = {'Gtt': {}, 'ttbar': {}, 'singletop': {}, 'ttbarV': {}, 'Zjets': {}, 'Wjets':{}}

groups = {'diboson': {'SR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}}, 
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}}, 
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}}, 
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}, 
                      'CR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}}, 
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}}, 
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}},
          'ttbarV':  {'SR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}},
                      'CR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}},
          'Zjets':   {'SR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}},
                      'CR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}},
          'Wjets':   {'SR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}},
                      'CR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}},
          'ttbar':   {'SR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}},
                      'CR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}},
         'singletop':{'SR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}},
                      'CR': {1: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             2: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             3: {'scaled': {}, 'raw': {}, 'weighted': {}},
                             4: {'scaled': {}, 'raw': {}, 'weighted': {}}}}}

# get the did to group mapping
files = glob.glob(os.path.join(pathToFiles, "*.root"))
#p = re.compile(os.path.join(pathToFiles, r'.*(\d{6}).*root'))
did_to_group = {}

#for f in files:
#  group, did = p.search(f).groups()
#  if 'ttbar' in group: group = 'ttbar'
#  did_to_group[did] = group

did_to_group['361081'] = 'diboson'
did_to_group['361082'] = 'diboson'
did_to_group['361083'] = 'diboson'
did_to_group['361084'] = 'diboson'
did_to_group['361085'] = 'diboson'
did_to_group['361086'] = 'diboson'
did_to_group['361087'] = 'diboson'

did_to_group['361300'] = 'Wjets'
did_to_group['361301'] = 'Wjets'
did_to_group['361302'] = 'Wjets'
did_to_group['361303'] = 'Wjets'
did_to_group['361304'] = 'Wjets'
did_to_group['361305'] = 'Wjets'
did_to_group['361306'] = 'Wjets'
did_to_group['361307'] = 'Wjets'
did_to_group['361308'] = 'Wjets'
did_to_group['361309'] = 'Wjets'
did_to_group['361310'] = 'Wjets'
did_to_group['361311'] = 'Wjets'
did_to_group['361312'] = 'Wjets'
did_to_group['361313'] = 'Wjets'
did_to_group['361314'] = 'Wjets'
did_to_group['361315'] = 'Wjets'
did_to_group['361316'] = 'Wjets'
did_to_group['361317'] = 'Wjets'
did_to_group['361318'] = 'Wjets'
did_to_group['361319'] = 'Wjets'
did_to_group['361320'] = 'Wjets'
did_to_group['361321'] = 'Wjets'
did_to_group['361322'] = 'Wjets'
did_to_group['361323'] = 'Wjets'
did_to_group['361324'] = 'Wjets'
did_to_group['361325'] = 'Wjets'
did_to_group['361326'] = 'Wjets'
did_to_group['361327'] = 'Wjets'
did_to_group['361328'] = 'Wjets'
did_to_group['361329'] = 'Wjets'
did_to_group['361330'] = 'Wjets'
did_to_group['361331'] = 'Wjets'
did_to_group['361332'] = 'Wjets'
did_to_group['361333'] = 'Wjets'
did_to_group['361334'] = 'Wjets'
did_to_group['361335'] = 'Wjets'
did_to_group['361336'] = 'Wjets'
did_to_group['361337'] = 'Wjets'
did_to_group['361338'] = 'Wjets'
did_to_group['361339'] = 'Wjets'
did_to_group['361340'] = 'Wjets'
did_to_group['361341'] = 'Wjets'
did_to_group['361342'] = 'Wjets'
did_to_group['361343'] = 'Wjets'
did_to_group['361344'] = 'Wjets'
did_to_group['361345'] = 'Wjets'
did_to_group['361346'] = 'Wjets'
did_to_group['361347'] = 'Wjets'
did_to_group['361348'] = 'Wjets'
did_to_group['361349'] = 'Wjets'
did_to_group['361350'] = 'Wjets'
did_to_group['361351'] = 'Wjets'
did_to_group['361352'] = 'Wjets'
did_to_group['361353'] = 'Wjets'
did_to_group['361354'] = 'Wjets'
did_to_group['361355'] = 'Wjets'
did_to_group['361356'] = 'Wjets'
did_to_group['361357'] = 'Wjets'
did_to_group['361358'] = 'Wjets'
did_to_group['361359'] = 'Wjets'
did_to_group['361360'] = 'Wjets'
did_to_group['361361'] = 'Wjets'
did_to_group['361362'] = 'Wjets'
did_to_group['361363'] = 'Wjets'
did_to_group['361364'] = 'Wjets'
did_to_group['361365'] = 'Wjets'
did_to_group['361366'] = 'Wjets'
did_to_group['361367'] = 'Wjets'
did_to_group['361368'] = 'Wjets'
did_to_group['361369'] = 'Wjets'
did_to_group['361370'] = 'Wjets'
did_to_group['361371'] = 'Wjets'

did_to_group['361372'] = 'Zjets'
did_to_group['361373'] = 'Zjets'
did_to_group['361374'] = 'Zjets'
did_to_group['361375'] = 'Zjets'
did_to_group['361376'] = 'Zjets'
did_to_group['361377'] = 'Zjets'
did_to_group['361378'] = 'Zjets'
did_to_group['361379'] = 'Zjets'
did_to_group['361380'] = 'Zjets'
did_to_group['361381'] = 'Zjets'
did_to_group['361382'] = 'Zjets'
did_to_group['361383'] = 'Zjets'
did_to_group['361384'] = 'Zjets'
did_to_group['361385'] = 'Zjets'
did_to_group['361386'] = 'Zjets'
did_to_group['361387'] = 'Zjets'
did_to_group['361388'] = 'Zjets'
did_to_group['361389'] = 'Zjets'
did_to_group['361390'] = 'Zjets'
did_to_group['361391'] = 'Zjets'
did_to_group['361392'] = 'Zjets'
did_to_group['361393'] = 'Zjets'
did_to_group['361394'] = 'Zjets'
did_to_group['361395'] = 'Zjets'
did_to_group['361396'] = 'Zjets'
did_to_group['361397'] = 'Zjets'
did_to_group['361398'] = 'Zjets'
did_to_group['361399'] = 'Zjets'
did_to_group['361400'] = 'Zjets'
did_to_group['361401'] = 'Zjets'
did_to_group['361402'] = 'Zjets'
did_to_group['361403'] = 'Zjets'
did_to_group['361404'] = 'Zjets'
did_to_group['361405'] = 'Zjets'
did_to_group['361406'] = 'Zjets'
did_to_group['361407'] = 'Zjets'
did_to_group['361408'] = 'Zjets'
did_to_group['361409'] = 'Zjets'
did_to_group['361410'] = 'Zjets'
did_to_group['361411'] = 'Zjets'
did_to_group['361412'] = 'Zjets'
did_to_group['361413'] = 'Zjets'
did_to_group['361414'] = 'Zjets'
did_to_group['361415'] = 'Zjets'
did_to_group['361416'] = 'Zjets'
did_to_group['361417'] = 'Zjets'
did_to_group['361418'] = 'Zjets'
did_to_group['361419'] = 'Zjets'
did_to_group['361420'] = 'Zjets'
did_to_group['361421'] = 'Zjets'
did_to_group['361422'] = 'Zjets'
did_to_group['361423'] = 'Zjets'
did_to_group['361424'] = 'Zjets'
did_to_group['361425'] = 'Zjets'
did_to_group['361426'] = 'Zjets'
did_to_group['361427'] = 'Zjets'
did_to_group['361428'] = 'Zjets'
did_to_group['361429'] = 'Zjets'
did_to_group['361430'] = 'Zjets'
did_to_group['361431'] = 'Zjets'
did_to_group['361432'] = 'Zjets'
did_to_group['361433'] = 'Zjets'
did_to_group['361434'] = 'Zjets'
did_to_group['361435'] = 'Zjets'
did_to_group['361436'] = 'Zjets'
did_to_group['361437'] = 'Zjets'
did_to_group['361438'] = 'Zjets'
did_to_group['361439'] = 'Zjets'
did_to_group['361440'] = 'Zjets'
did_to_group['361441'] = 'Zjets'
did_to_group['361442'] = 'Zjets'
did_to_group['361443'] = 'Zjets'
did_to_group['361444'] = 'Zjets'
did_to_group['361445'] = 'Zjets'
did_to_group['361446'] = 'Zjets'
did_to_group['361447'] = 'Zjets'
did_to_group['361448'] = 'Zjets'
did_to_group['361449'] = 'Zjets'
did_to_group['361450'] = 'Zjets'
did_to_group['361451'] = 'Zjets'
did_to_group['361452'] = 'Zjets'
did_to_group['361453'] = 'Zjets'
did_to_group['361454'] = 'Zjets'
did_to_group['361455'] = 'Zjets'
did_to_group['361456'] = 'Zjets'
did_to_group['361457'] = 'Zjets'
did_to_group['361458'] = 'Zjets'
did_to_group['361459'] = 'Zjets'
did_to_group['361460'] = 'Zjets'
did_to_group['361461'] = 'Zjets'
did_to_group['361462'] = 'Zjets'
did_to_group['361463'] = 'Zjets'
did_to_group['361464'] = 'Zjets'
did_to_group['361465'] = 'Zjets'
did_to_group['361466'] = 'Zjets'
did_to_group['361467'] = 'Zjets'

did_to_group['370100'] = 'Gtt'
did_to_group['370101'] = 'Gtt'
did_to_group['370102'] = 'Gtt'
did_to_group['370103'] = 'Gtt'
did_to_group['370104'] = 'Gtt'
did_to_group['370105'] = 'Gtt'
did_to_group['370106'] = 'Gtt'
did_to_group['370107'] = 'Gtt'
did_to_group['370108'] = 'Gtt'
did_to_group['370109'] = 'Gtt'
did_to_group['370110'] = 'Gtt'
did_to_group['370111'] = 'Gtt'
did_to_group['370112'] = 'Gtt'
did_to_group['370113'] = 'Gtt'
did_to_group['370114'] = 'Gtt'
did_to_group['370115'] = 'Gtt'
did_to_group['370116'] = 'Gtt'
did_to_group['370117'] = 'Gtt'
did_to_group['370118'] = 'Gtt'
did_to_group['370119'] = 'Gtt'
did_to_group['370120'] = 'Gtt'
did_to_group['370121'] = 'Gtt'
did_to_group['370122'] = 'Gtt'
did_to_group['370123'] = 'Gtt'
did_to_group['370124'] = 'Gtt'
did_to_group['370125'] = 'Gtt'
did_to_group['370126'] = 'Gtt'
did_to_group['370127'] = 'Gtt'
did_to_group['370128'] = 'Gtt'
did_to_group['370129'] = 'Gtt'
did_to_group['370130'] = 'Gtt'
did_to_group['370131'] = 'Gtt'
did_to_group['370132'] = 'Gtt'
did_to_group['370133'] = 'Gtt'
did_to_group['370134'] = 'Gtt'
did_to_group['370135'] = 'Gtt'
did_to_group['370136'] = 'Gtt'
did_to_group['370137'] = 'Gtt'
did_to_group['370138'] = 'Gtt'
did_to_group['370139'] = 'Gtt'
did_to_group['370140'] = 'Gtt'
did_to_group['370141'] = 'Gtt'
did_to_group['370142'] = 'Gtt'
did_to_group['370143'] = 'Gtt'
did_to_group['370144'] = 'Gtt'
did_to_group['370145'] = 'Gtt'
did_to_group['370146'] = 'Gtt'
did_to_group['370147'] = 'Gtt'
did_to_group['370148'] = 'Gtt'
did_to_group['370149'] = 'Gtt'
did_to_group['370150'] = 'Gtt'
did_to_group['370151'] = 'Gtt'
did_to_group['370152'] = 'Gtt'
did_to_group['370153'] = 'Gtt'
did_to_group['370154'] = 'Gtt'
did_to_group['370155'] = 'Gtt'
did_to_group['370156'] = 'Gtt'
did_to_group['370157'] = 'Gtt'
did_to_group['370158'] = 'Gtt'
did_to_group['370159'] = 'Gtt'
did_to_group['370160'] = 'Gtt'
did_to_group['370161'] = 'Gtt'
did_to_group['370162'] = 'Gtt'
did_to_group['370163'] = 'Gtt'
did_to_group['370164'] = 'Gtt'
did_to_group['370165'] = 'Gtt'
did_to_group['370166'] = 'Gtt'
did_to_group['370167'] = 'Gtt'
did_to_group['370168'] = 'Gtt'
did_to_group['370169'] = 'Gtt'
did_to_group['370170'] = 'Gtt'
did_to_group['370171'] = 'Gtt'
did_to_group['370172'] = 'Gtt'
did_to_group['370173'] = 'Gtt'
did_to_group['370174'] = 'Gtt'
did_to_group['370175'] = 'Gtt'
did_to_group['370176'] = 'Gtt'
did_to_group['370177'] = 'Gtt'
did_to_group['370178'] = 'Gtt'
did_to_group['370179'] = 'Gtt'
did_to_group['370180'] = 'Gtt'
did_to_group['370181'] = 'Gtt'
did_to_group['370182'] = 'Gtt'
did_to_group['370183'] = 'Gtt'
did_to_group['370184'] = 'Gtt'
did_to_group['370185'] = 'Gtt'
did_to_group['370186'] = 'Gtt'
did_to_group['370187'] = 'Gtt'
did_to_group['370424'] = 'Gtt'
did_to_group['370426'] = 'Gtt'
did_to_group['370429'] = 'Gtt'
did_to_group['370436'] = 'Gtt'
did_to_group['370442'] = 'Gtt'
did_to_group['370450'] = 'Gtt'
did_to_group['370524'] = 'Gtt'
did_to_group['370529'] = 'Gtt'

did_to_group['407009'] = 'ttbar'
did_to_group['407010'] = 'ttbar'
did_to_group['407011'] = 'ttbar'

did_to_group['410011'] = 'singletop'
did_to_group['410012'] = 'singletop'
did_to_group['410013'] = 'singletop'
did_to_group['410014'] = 'singletop'

did_to_group['410066'] = 'ttbarV'
did_to_group['410067'] = 'ttbarV'
did_to_group['410068'] = 'ttbarV'
did_to_group['410069'] = 'ttbarV'
did_to_group['410069'] = 'ttbarV'
did_to_group['410070'] = 'ttbarV'
did_to_group['410071'] = 'ttbarV'
did_to_group['410072'] = 'ttbarV'
did_to_group['410073'] = 'ttbarV'
did_to_group['410074'] = 'ttbarV'
did_to_group['410075'] = 'ttbarV'
did_to_group['410076'] = 'ttbarV'
did_to_group['410080'] = 'ttbarV' # 4tops SM
did_to_group['341177'] = 'ttbarV' # ttH

for regionID in range(1, 5):
  for fname in glob.glob("CR{0:d}Cuts/*.json".format(regionID))+glob.glob("SR{0:d}Cuts/*.json".format(regionID)):
    did = os.path.basename(fname).split('.')[0]

    #print "DEBUG\tDID is\t%s" %did

    # figure out if we're using SR or CR
    region='CR'
    if 'SR' in os.path.basename(os.path.dirname(fname)): region='SR'

    #print "DEBUG\tregion is is\t%s" %region
    #print "DEBUG\tregionID is is\t%s" %regionID

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
        value = data[count_type]*sf
        groups[did_to_group[did]][region][regionID][count_type] = data[count_type]*sf
#       groups[did_to_group[did]][region][regionID][count_type] += data[count_type]*sf

def getValues(group, groups):
  return [group] + [groups[group][region][i][index] for region in ['SR', 'CR'] for i in range(1, 5)]

for index, typeBkgd in zip(count_types, ['raw', 'weighted', 'scaled ({0:0.4f}ifb)'.format(scaleFactor)]):
  sumValues = [0]*8
  print("{0: ^150s}".format(typeBkgd))
  printStr = "{{0:12}}{0:s}1{0:s}2{0:s}3{0:s}4{1:s}1{1:s}2{1:s}3{1:s}4".format("\t{1:>9}", "\t{2:>9}")
  print(printStr.format("GROUP", "SR", "CR"))
  for group in sorted(groups):
    values = getValues(group, groups)
    print values
    valueStr = "{{0:12}}\t{{1:{0:s}}}\t{{2:{0:s}}}\t{{3:{0:s}}}\t{{4:{0:s}}}\t{{5:{0:s}}}\t{{6:{0:s}}}\t{{7:{0:s}}}\t{{8:{0:s}}}".format("10.4f")
    print(valueStr.format(*values))
    #print(valueStr)
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
