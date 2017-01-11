import argparse
import subprocess
import os

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))

parser.add_argument('summaries', type=str, nargs='+', metavar='<summary.json>', help='summary files for a given set of signal regions')
parser.add_argument('-o', '--output', required=False, type=str, dest='output', help='Output json to make', default='summary.json')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

import json
import operator

summaries = [sorted(json.load(file(f)), key=operator.itemgetter('did')) for f in args.summaries]

# find the winning SR
# TODO: match by DID and only use the winning of those which have the DID in common
winning_items = (max(enumerate(row), key=lambda i: i[1]['significance']) for row in zip(*summaries))

winning_summary = []
for index, summary in winning_items:
  summary['region'] = os.path.basename(os.path.splitext(args.summaries[index])[0])
  winning_summary.append(summary)

with open(args.output, 'w+') as f:
  f.write(json.dumps(sorted(winning_summary, key=operator.itemgetter('did')), sort_keys=True, indent=4))
