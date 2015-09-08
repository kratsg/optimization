'''
supercuts_file = 'supercuts_baseline.json'
hash_dir = 'outputHash_baseline_1'
sig_dir = 'baselineSignificances_1'
'''

'''
supercuts_file = 'supercuts_massScan.json'
hash_dir = 'outputHash_massScan_1'
sig_dir = 'massScanSignificances_1'
'''

'''
supercuts_file = 'supercuts_no_mTb.json'
hash_dir = 'outputHash_nomTb_10'
sig_dir = 'nomTbSignificances_10'
'''

'''
supercuts_file = 'supercuts_fixedMassScan.json'
hash_dir = 'outputHash_fixedMassScan_1'
sig_dir = 'fixedMassScanSignificances_1'
'''

import csv,glob,re,json
def get_hashes():
  mdict = {}
  with open('mass_windows.txt', 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    m = list(reader)
    mdict = {l[0]: [l[1],l[2],l[3]] for l in m}

  def masses(did):
    mlist = mdict[did]
    mglue = mlist[0]
    mstop = mlist[1]
    mlsp = mlist[2]
    return mglue,mstop,mlsp

  filenames = glob.glob(sig_dir+'/s*.b*.json')
  regex = re.compile('s(\d{6})\.b.*\.json')
  dids = []
  sigs = []
  for filename in filenames:
    with open(filename) as f:
      sigs.append(json.load(f)[0]['hash'])
      did = regex.search(filename)
      dids.append(did.group(1))

  plot_array=[]
  for did,sig in zip(dids,sigs):
    mgluino,mstop,mlsp = masses(did)
    row = [mgluino,mstop,mlsp,sig]
    if int(mstop) == 5000: plot_array.append(row)

  return plot_array

import subprocess
array = get_hashes()
bashCommand = 'python optimize.py hash '
for row in array:
  h = row[3]
  bashCommand += h + ' '
bashCommand += '--supercuts ' + supercuts_file + ' -b'
bashCommand += ' -o ' + hash_dir
print bashCommand
subprocess.call(bashCommand,shell=True)

import numpy
nparray = numpy.array(array)
import pdb
numpy.savetxt(hash_dir+'/mass_windows_hashes.txt',nparray,delimiter='\t',fmt='%s')
