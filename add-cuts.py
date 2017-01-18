import os
import csv
import json

def add_cuts(cuts_left, cuts_right):
  output_dict = {}
  for h in cuts_left.keys():
    output_dict[h] = dict((k, cuts_left[h][k]+cuts_right[h][k]) for k in ["raw", "scaled", "weighted"])
  return output_dict

if __name__ == '__main__':

  import argparse
  import subprocess

  class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    pass

  __version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
  __short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

  parser = argparse.ArgumentParser(description='Left-add multiple cut files together by hash. It will use the first cut file as the list of hashes. Author: G. Stark. v.{0}'.format(__version__),
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))

  parser.add_argument('cuts', type=str, nargs='+', metavar='<DID.json>', help='cut files to merge')
  parser.add_argument('-o', '--output', required=True, type=str, dest='output', help='name the output json')

  # parse the arguments, throw errors if missing any
  args = parser.parse_args()

  output_cuts = reduce(lambda x,y: add_cuts(x, json.load(file(y))), args.cuts[1:], json.load(file(args.cuts[0])))

  with open(args.output, 'w+') as f:
    f.write(json.dumps(output_cuts, sort_keys=True, indent=4))
