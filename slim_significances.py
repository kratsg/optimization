import argparse
import subprocess
import os
import glob
import json

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('--significances', required=False, type=str, dest='significances', metavar='<folder>', help='folder of significance calculations', default='significances')
parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<folder>', help='folder to store output hash dumps', default='significances_slim')
parser.add_argument('-n', '--maxNum', required=False, type=int, dest='max_number', metavar='<n>', help='Maximum number of entries to keep', default=50)

# parse the arguments, throw errors if missing any
args = parser.parse_args()

if not os.path.exists(args.output_directory):
  os.makedirs(args.output_directory)
else:
  raise IOError("Output directory already exists: {0:s}".format(args.output_directory))


filenames = glob.glob(args.significances+'/s*.b*.json')
bkgdFiles = set()
for filename in filenames:
  bkgdFiles.add(os.path.join(os.path.dirname(filename), os.path.basename(filename).split('.b')[1]))
  with open(filename) as f:
    json.dump(json.load(f)[:50], file(os.path.join(args.output_directory, os.path.basename(filename)), 'w+'))

import shutil
for bkgdFile in bkgdFiles:
  shutil.copyfile(bkgdFile, os.path.join(args.output_directory, os.path.basename(bkgdFile)))
