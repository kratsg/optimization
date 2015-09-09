import argparse
import subprocess
import os

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: A. Cukierman, G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('--supercuts', required=True, type=str, dest='supercuts', metavar='<file.json>', help='json dict of supercuts to generate optimization cuts to apply')
parser.add_argument('--significances', required=True, type=str, dest='significances', metavar='<folder>', help='folder of significance calculations')
parser.add_argument('-o', '--output', required=False, type=str, dest='output', metavar='<folder>', help='folder to store output hash dumps')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

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

  filenames = glob.glob(args.significances+'/s*.b*.json')
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
bashCommand += '--supercuts ' + args.supercuts + ' -b'
bashCommand += ' -o ' + args.output
print bashCommand
subprocess.call(bashCommand,shell=True)

import numpy
nparray = numpy.array(array)
import pdb
numpy.savetxt(args.output+'/mass_windows_hashes.txt',nparray,delimiter='\t',fmt='%s')
