#!/usr/bin/env python

# @file:    optimize.py
# @purpose: read a ROOT file containing ntuples and attempt to find optimal cuts
# @author:  Giordon Stark <gstark@cern.ch>
# @date:    June 2015
#

# __future__ imports must occur at beginning of file
# redirect python output using the newer print function with file description
#   print(string, f=fd)
from __future__ import print_function
# used to redirect ROOT output
#   see http://stackoverflow.com/questions/21541238/get-ipython-doesnt-work-in-a-startup-script-for-ipython-ipython-notebook
import tempfile

import os, sys
# grab the stdout and have python write to this instead
# ROOT will write to the original stdout
STDOUT = os.fdopen(os.dup(sys.stdout.fileno()), 'w')

# for logging, set it up
import logging
root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler(STDOUT))
logger = logging.getLogger("optimize")

# import all libraries
import argparse
import subprocess
import json
import hashlib
import copy
import operator
import re
import fnmatch
import math
import yaml

'''
  with tempfile.NamedTemporaryFile() as tmpFile:
    if not args.debug:
      ROOT.gSystem.RedirectOutput(tmpFile.name, "w")

    # execute code here

    if not args.debug:
      ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")
'''

# Set up ROOT
import ROOT

#root_numpy
import root_numpy as rnp
import numpy as np


def format_arg_value(arg_val):
  """ Return a string representing a (name, value) pair.

  >>> format_arg_value(('x', (1, 2, 3)))
  'x=(1, 2, 3)'
  """
  arg, val = arg_val
  return "%s=%r" % (arg, val)

# http://wordaligned.org/articles/echo
def echo(*echoargs, **echokwargs):
  logger.debug(echoargs)
  logger.debug(echokwargs)
  def echo_wrap(fn):
    """ Echo calls to a function.

    Returns a decorated version of the input function which "echoes" calls
    made to it by writing out the function's name and the arguments it was
    called with.
    """

    # Unpack function's arg count, arg names, arg defaults
    code = fn.func_code
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]
    fn_defaults = fn.func_defaults or list()
    argdefs = dict(zip(argnames[-len(fn_defaults):], fn_defaults))

    def wrapped(*v, **k):
      # Collect function arguments by chaining together positional,
      # defaulted, extra positional and keyword arguments.
      positional = map(format_arg_value, zip(argnames, v))
      defaulted = [format_arg_value((a, argdefs[a]))
                   for a in argnames[len(v):] if a not in k]
      nameless = map(repr, v[argcount:])
      keyword = map(format_arg_value, k.items())
      args = positional + defaulted + nameless + keyword
      write("%s(%s)\n" % (fn.__name__, ", ".join(args)))
      return fn(*v, **k)
    return wrapped

  write = echokwargs.get('write', sys.stdout.write)
  if len(echoargs) == 1 and callable(echoargs[0]):
    return echo_wrap(echoargs[0])
  return echo_wrap

#@echo(write=logger.debug)
def apply_cut(arr, pivot, direction):
  """ Given a numpy array of values, apply a cut in the direction of expected signal

  >>> apply_cut(np.random.randn(100), 0, '>')  # only positive values (val > cut)
  >>> apply_cut(np.random.randn(100), 0, '<')  # only negative values (val < cut)
  """
  if pivot is None:
    return np.ones(arr.shape, dtype=bool)

  if direction == '<=':
    return arr <= pivot
  elif direction == '>=':
    return arr >= pivot
  elif direction == '<':
    return arr < pivot
  elif direction == '>':
    return arr > pivot
  else:
    return np.ones(arr.shape, dtype=bool)

#@echo(write=logger.debug)
def apply_cuts(arr, cuts):
  return reduce(np.bitwise_and, (apply_cut(arr[cut['branch']], cut.get('pivot', None), cut.get('signal_direction', None)) for cut in cuts))

#@echo(write=logger.debug)
def get_cut(superCuts, index=0):
  # reached bottom of iteration, yield what we've done
  if index >= len(superCuts): yield superCuts
  else:
    # start of iteration, make a copy of the input dictionary
    # if index == 0: superCuts = copy.deepcopy(superCuts)
    # reference to item
    item = superCuts[index]
    # are we doing a fixed cut? they should specify only pivot
    try:
      # if they don't want a fixed cut, then they need start, stop, step
      for pivot in np.arange(item['start'], item['stop'], item['step']):
        # set the pivot value
        item['pivot'] = pivot
        item['fixed'] = False
        # recursively call, yield the result which is the superCuts
        for cut in get_cut(superCuts, index+1): yield cut
    except KeyError:
      item['fixed'] = True
      for cut in get_cut(superCuts, index+1): yield cut

#@echo(write=logger.debug)
def get_cut_hash(cut):
  return hashlib.md5(str([sorted(obj.items()) for obj in cut])).hexdigest()

#@echo(write=logger.debug)
def count_events(tree, cuts, eventWeightBranch):
  events = tree[eventWeightBranch][apply_cuts(tree, cuts)]
  return events.size, np.sum(events).astype(float)

#@echo(write=logger.debug)
def get_did(filename):
  did_regex = re.compile('(\d{6,8})')
  m = did_regex.search(filename)
  if m is None: raise ValueError('Can\'t figure out the DID!')
  return m.group(1)

#@echo(write=logger.debug)
def get_scaleFactor(filename):
  did = get_did(filename)
  weights = yaml.load(file(args.weightsFile))
  weight = weights.get(did)
  if weight is None:
    raise KeyError("Could not find the weights for did=%s" % did)
  scaleFactor = 1.0
  cutflow = weight.get('num events')
  if args.debug: logger.log(25,"Cutflow: " + str(cutflow))
  if cutflow == 0:
    raise ValueError('Num events = 0!')
  scaleFactor /= cutflow 
  if args.debug: logger.log(25,"ScaleFactor: " + str(scaleFactor))
  scaleFactor *= weight.get('cross section')
  if args.debug: logger.log(25,"ScaleFactor: " + str(scaleFactor))
  if args.debug: logger.log(25,"Cross Section: " + str(weight.get('cross section')))
  scaleFactor *= weight.get('filter efficiency')
  if args.debug: logger.log(25,"ScaleFactor: " + str(scaleFactor))
  if args.debug: logger.log(25,"Filter Efficiency: " + str(weight.get('filter efficiency')))
  scaleFactor *= weight.get('k-factor')
  if args.debug: logger.log(25,"ScaleFactor: " + str(scaleFactor))
  if args.debug: logger.log(25,"k-factor: " + str(weight.get('k-factor')))
  scaleFactor *= weights.get('global_luminosity') * 1000 #to account for units on luminosity
  if args.debug: logger.log(25,"ScaleFactor: " + str(scaleFactor))
  if args.debug: logger.log(25,"lumi: " + str(weights.get('global_luminosity')))
  return scaleFactor
  

#@echo(write=logger.debug)
def get_significance(signal, bkgd, cuts, eventWeightBranch, insignificanceThreshold, bkgdUncertainty, bkgdStatUncertainty, signal_scale, bkgd_scale):
  numSignal, weightedSignal = count_events(signal, cuts, eventWeightBranch)
  numBkgd, weightedBkgd = count_events(bkgd, cuts, eventWeightBranch)
  
  # apply scale factors and luminosity
  numSignal = numSignal 
  weightedSignal = weightedSignal
  scaledSignal = weightedSignal * signal_scale
  numBkgd = numBkgd 
  weightedBkgd = weightedBkgd
  scaledBkgd = weightedBkgd * bkgd_scale

  # dict containing what we want to record in the output
  sigDetails = {'signal': numSignal, 'signalWeighted': weightedSignal,'signalScaled': scaledSignal, 'bkgd': numBkgd, 'bkgdWeighted': weightedBkgd, 'bkgdScaled': scaledBkgd}

  # if not enough events, return string of which one did not have enough
  if scaledSignal < insignificanceThreshold:
    sigDetails['insignificance'] = "signal"
    sig = 0
  elif numBkgd < 1/(pow(bkgdStatUncertainty,2)): #require sqrt(numBkgd)/numBkgd < bkgdStatUncertainty
    sigDetails['insignificance'] = "bkgd"
    sig = 0
  else:
    # otherwise, calculate!
    sig = ROOT.RooStats.NumberCountingUtils.BinomialExpZ(scaledSignal, scaledBkgd, bkgdUncertainty)
  return sig, sigDetails

#@echo(write=logger.debug)
def get_ttrees(tree_name, signalFilenames, bkgdFilenames, eventWeightBranch):
  # this is a dict that holds all the trees
  trees = {'signal': None, 'bkgd': None}
  fnames = {'signal': signalFilenames, 'bkgd': bkgdFilenames}

  for group in ['signal', 'bkgd']:
    logger.info("Initializing TChain: {0}".format(group))
    # start by making a TChain
    trees[group] = ROOT.TChain(tree_name)
    for fname in fnames.get(group, []):
      if not os.path.isfile(fname):
        raise ValueError('The supplied input file `{0}` does not exist or I cannot find it.'.format(fname))
      else:
        logger.info("\tAdding {0}".format(fname))
        trees[group].Add(fname)

    # Print some information
    logger.info('\tNumber of input events: %s' % trees[group].GetEntries())

  # make sure the branches are compatible between the two
  signalBranches = set(i.GetName() for i in trees['signal'].GetListOfBranches())
  bkgdBranches = set(i.GetName() for i in trees['bkgd'].GetListOfBranches())
  if not signalBranches == bkgdBranches:
    raise ValueError('The signal and background trees do not have the same branches!')

  if not eventWeightBranch in signalBranches:
    raise ValueError('The event weight branch does not exist: {0}'.format(eventWeightBranch))

  return trees

#@echo(write=logger.debug)
def read_supercuts_file(filename):
  logger.info("Reading supercuts file {0}".format(filename))
  logger.info("\tOpening")
  with open(filename) as f:
    supercuts = json.load(f)

  logger.info("\tLoaded")
  branches = set([supercut['branch'] for supercut in supercuts])
  try:
    for supercut in supercuts:
      branches.remove(supercut['branch'])
  except KeyError:
    raise KeyError("Found more than one supercut definition on {0}".format(supercut['branch']))

  logger.info("\tFound {1:d} supercut definitions".format(filename, len(supercuts)))
  return supercuts

#@echo(write=logger.debug)
def do_optimize(args):
  if os.path.isfile(args.output_filename):
    raise IOError("Output file already exists: {0}".format(args.output_filename))

  # this is a dict that holds all the trees
  trees = get_ttrees(args.tree_name, args.signal, args.bkgd, args.eventWeightBranch)

  # read the cuts file
  data = read_supercuts_file(args.supercuts)
  branchesToRead = [args.eventWeightBranch]+[i['branch'] for i in data]
  logger.info("Loading {0:d} branches ({1:d} branches + {2:s}) from the signal and bkgd ttrees".format(len(branchesToRead), len(branchesToRead)-1, args.eventWeightBranch))

  # get signal and background trees, only need some of the branches (not all!)
  signal = rnp.tree2array(trees['signal'], branches=branchesToRead)
  bkgd = rnp.tree2array(trees['bkgd'], branches=branchesToRead)

  # start optimizing
  logger.log(25, "Calculating significance for a variety of cuts")

  # get scale factors
  signal_scale = get_scaleFactor(args.signal[0])
  bkgd_scale = get_scaleFactor(args.bkgd[0])

  # hold list of dictionaries {'hash': <sha1>, 'significance': <significance>}
  significances = []
  for cut in get_cut(copy.deepcopy(data)):
    cut_hash = get_cut_hash(cut)
    cut_significance, sig_details = get_significance(signal, bkgd, cut, args.eventWeightBranch, args.insignificanceThreshold, args.bkgdUncertainty, args.bkgdStatUncertainty, signal_scale, bkgd_scale)

    significances.append({'hash': cut_hash, 'significance': 0 if math.isinf(cut_significance) else round(cut_significance, 4), 'details': sig_details})
    #logger.info("\t{0:32s}\t{1:10.4f}".format(cut_hash, cut_significance))

  logger.log(25, "Calculated significance for {0:d} cuts".format(len(significances)))

  with open(args.output_filename, 'w+') as f:
    f.write(json.dumps(sorted(significances, key=operator.itemgetter('significance'), reverse=True), sort_keys=True, indent=4))

  return True

#@echo(write=logger.debug)
def match_branch(branch, list_of_branches):
  if branch in list_of_branches: return True
  for b in list_of_branches:
    if re.compile(fnmatch.translate(b)).search(branch): return True
  return False

#@echo(write=logger.debug)
def do_generate(args):
  if os.path.isfile(args.output_filename):
    raise IOError("Output file already exists: {0}".format(args.output_filename))

  # this is a dict that holds all the trees
  trees = get_ttrees(args.tree_name, args.signal, args.bkgd, args.eventWeightBranch)

  # list of branches to loop over
  branches=[i.GetName() for i in trees['signal'].GetListOfBranches() if not i.GetName() == args.eventWeightBranch]

  # get signal and background trees
  signal = rnp.tree2array(trees['signal'], branches=branches)
  bkgd = rnp.tree2array(trees['bkgd'], branches=branches)

  supercuts = []

  for b in branches:
    if match_branch(b, args.skip_branches):
      logger.log(25, "{0:32s}:\tSkipping as requested".format(b))
      continue

    skipSignal = signal[b] < args.globalMinVal
    skipBkgd = bkgd[b] < args.globalMinVal

    signalPercentile = np.percentile(signal[b][~skipSignal], [0., 25., 50., 75., 100.])
    bkgdPercentile = np.percentile(bkgd[b][~skipBkgd], [0., 25., 50., 75., 100.])
    prelimStr = "{0}\n\tSignal ({1:6d} ignored):\t{2[0]:12.4f}\t{2[1]:12.4f}\t{2[2]:12.4f}\t{2[3]:12.4f}\t{2[4]:12.4f}\n\tBkgd   ({3:6d} ignored):\t{4[0]:12.4f}\t{4[1]:12.4f}\t{4[2]:12.4f}\t{4[3]:12.4f}\t{4[4]:12.4f}"

    logger.info(prelimStr.format(b, np.sum(skipSignal), signalPercentile, np.sum(skipBkgd), bkgdPercentile))

    if signalPercentile[2] > bkgdPercentile[2]: signal_direction = '>'
    else: signal_direction = '<'

    if match_branch(b, args.fixed_branches):
      supercuts.append({'branch': b,
                        'pivot': signalPercentile[2],
                        'signal_direction': signal_direction})
    else:
      if signal_direction == '>':
        start = signalPercentile[0]
        stop = signalPercentile[-1]
      else:
        start = signalPercentile[-1]
        stop = signalPercentile[0]
      supercuts.append({'branch': b,
                        'start': int(start),
                        'stop': int(stop),
                        'step': int((stop-start)/10.),
                        'signal_direction': signal_direction})


  with open(args.output_filename, 'w+') as f:
    f.write(json.dumps(sorted(supercuts, key=operator.itemgetter('branch')), sort_keys=True, indent=4))


  return True

#@echo(write=logger.debug)
def do_hash(args):
  # first start by making the output directory
  if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
  else:
    raise IOError("Output directory already exists: {0}".format(args.output_directory))

  # next, read in the supercuts file
  data = read_supercuts_file(args.supercuts)

  logger.info("Finding cuts for {0:d} hashes.".format(len(args.hash_values)))
  # now loop over all cuts until we find all the hashes
  for cut in get_cut(copy.deepcopy(data)):
    cut_hash = get_cut_hash(cut)
    if cut_hash in args.hash_values:
      with open(os.path.join(args.output_directory, "{0}.json".format(cut_hash)), 'w+') as f:
        f.write(json.dumps([{k: v for k, v in d.iteritems() if k in ['branch', 'pivot', 'signal_direction', 'fixed']} for d in cut], sort_keys=True, indent=4))
      args.hash_values.remove(cut_hash)
      logger.info("\tFound cut for hash {0:32s}. {1:d} hashes left.".format(cut_hash, len(args.hash_values)))
    if not args.hash_values: break
  return True

if __name__ == "__main__":
  class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    pass

  class _HelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
      parser.print_help()
      parser.exit()

  class _AllHelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
      parser.print_help()
      # retrieve subparsers from parser
      subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]
      # there will probably only be one subparser_action,
      # but better save than sorry
      for subparsers_action in subparsers_actions:
        # get all subparsers and print help
        for choice, subparser in subparsers_action.choices.items():
          print("-"*80)
          print("Subparser '{}'".format(choice))
          print(subparser.format_help())
      parser.exit()

  __version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
  __short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

  parser = argparse.ArgumentParser(add_help=False, description='Author: Giordon Stark. v.{0}'.format(__version__),
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
                                   epilog='This is the top-level. You have no power here. If you want to get started, run `%(prog)s optimize -h`.')
  parser.add_argument('-h', '--help', action=_HelpAction, help='show this help message and exit')  # add custom help
  parser.add_argument('-a', '--allhelp', action=_AllHelpAction, help='show this help message and all subcommand help messages and exit')  # add custom help

  ''' subparsers have common parameters '''
  main_parser = argparse.ArgumentParser(add_help=False)
  optimize_hash_parser = argparse.ArgumentParser(add_help=False)
  optimize_generate_parser = argparse.ArgumentParser(add_help=False)

  requiredNamed_optimize_hash = optimize_hash_parser.add_argument_group('required named arguments')
  requiredNamed_optimize_generate = optimize_generate_parser.add_argument_group('required named arguments')

  # general arguments for all
  main_parser.add_argument('-v','--verbose', dest='verbose', action='count', default=0, help='Enable verbose output of various levels. Use --debug to enable output for debugging.')
  main_parser.add_argument('--debug', dest='debug', action='store_true', help='Enable ROOT output and full-on debugging. Use this if you need to debug the application.')
  main_parser.add_argument('-b', '--batch', dest='batch_mode', action='store_true', help='Enable batch mode for ROOT.')
  # positional argument, require the first argument to be the input filename
  requiredNamed_optimize_generate.add_argument('--signal', required=True, type=str, nargs='+', metavar='<file.root>', help='ROOT files containing the signal ttrees')
  requiredNamed_optimize_generate.add_argument('--bkgd', required=True, type=str, nargs='+', metavar='<file.root>', help='ROOT files containing the background ttrees')
  requiredNamed_optimize_hash.add_argument('--supercuts', required=True, type=str, dest='supercuts', metavar='<file.json>', help='json dict of supercuts to generate optimization cuts over signal and bkgd')
  # these are options allowing for various additional configurations in filtering container and types to dump
  optimize_generate_parser.add_argument('--tree', type=str, required=False, dest='tree_name', metavar='<tree name>', help='name of the tree containing the ntuples', default='oTree')
  optimize_generate_parser.add_argument('--eventWeight', type=str, required=False, dest='eventWeightBranch', metavar='<branch name>', help='name of event weight branch in the ntuples. It must exist.', default='event_weight')

  ''' add subparsers '''
  subparsers = parser.add_subparsers(dest='command', help='actions available')
  # needs: signal, bkgd, tree, eventWeight, bkgdUncertainty, insignificanceThreshold, cuts
  optimize_parser = subparsers.add_parser("optimize", parents=[main_parser, optimize_hash_parser, optimize_generate_parser],
                                          description='Process ROOT ntuples and Optimize Cuts. v.{0}'.format(__version__),
                                          usage='%(prog)s  --signal=signal.root [..] --bkgd=bkgd.root [...] --supercuts=supercuts.json [options]', help='Find optimal cuts',
                                          formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                          epilog='optimize will take in signal, background, supercuts and calculate the significances for all cuts possible.')
  optimize_parser.add_argument('-o', '--output', required=False, type=str, dest='output_filename', metavar='<file.json>', help='output json file to store the significances computed', default='significances.json')
  optimize_parser.add_argument('--bkgdUncertainty', type=float, required=False, dest='bkgdUncertainty', metavar='<sigma>', help='background uncertainty for calculating significance', default=0.3)
  optimize_parser.add_argument('--bkgdStatUncertainty', type=float, required=False, dest='bkgdStatUncertainty', metavar='<sigma>', help='background statistical uncertainty for calculating significance', default=0.3)
  optimize_parser.add_argument('--insignificance', type=int, required=False, dest='insignificanceThreshold', metavar='<min events>', help='minimum number of signal events for calculating significance', default=2)
  optimize_parser.add_argument('--weightsFile', type=str, required=False, dest='weightsFile', metavar='<weights file>', help='yml file containing weights by DID', default='weights.yml')

  # needs: signal, bkgd, tree, globalMinVal, eventWeight
  generate_parser = subparsers.add_parser("generate", parents=[main_parser, optimize_generate_parser],
                                          description='Given the ROOT ntuples, generate a supercuts.json template. v.{0}'.format(__version__),
                                          usage='%(prog)s --signal=signal.root [..] --bkgd=bkgd.root [...] [options]', help='Write supercuts template',
                                          formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                          epilog='generate will take in signal, background and generate the supercuts template file for you to edit and use (rather than making it by hand)')
  generate_parser.add_argument('-o', '--output', required=False, type=str, dest='output_filename', metavar='<file.json>', help='output json file to store the generated supercuts template', default='supercuts.json')
  generate_parser.add_argument('--globalMinVal', type=float, required=False, dest='globalMinVal', metavar='<min val>', help='minimum value when analyzing branch-by-branch.', default=-90.0)
  generate_parser.add_argument('--fixedBranches', type=str, nargs='+', required=False, dest='fixed_branches', metavar='<branch name>', help='branches that should have a fixed cut. can use wildcards', default=[])
  generate_parser.add_argument('--skipBranches', type=str, nargs='+', required=False, dest='skip_branches', metavar='<branch name>', help='branches that should be skipped. can use wildcards', default=[])

  # needs: cuts
  hash_parser = subparsers.add_parser("hash", parents=[main_parser, optimize_hash_parser],
                                      description='Given a hash from optimization, dump the cuts associated with it. v.{0}'.format(__version__),
                                      usage='%(prog)s <hash> [<hash> ...] --supercuts=supercuts.json [options]', help='Translate hash to cut',
                                      formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                      epilog='hash will take in a list of hashes and dump the cuts associated with them')
  hash_parser.add_argument('hash_values', type=str, nargs='+', metavar='<hash>', help='Specify a hash to look up the cut for')
  hash_parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<directory>', help='output directory to store the <hash>.json files', default='outputHash')

  # set the functions that get called with the given arguments
  optimize_parser.set_defaults(func=do_optimize)
  generate_parser.set_defaults(func=do_generate)
  hash_parser.set_defaults(func=do_hash)

  # parse the arguments, throw errors if missing any
  args = parser.parse_args()

  try:
    # start execution of actual program
    import timing

    # set verbosity for python printing
    if args.verbose < 5:
      logger.setLevel(25 - args.verbose*5)
    else:
      logger.setLevel(logging.NOTSET + 1)

    with tempfile.NamedTemporaryFile() as tmpFile:
      if not args.debug:
        ROOT.gSystem.RedirectOutput(tmpFile.name, "w")

      # if flag is shown, set batch_mode to true, else false
      ROOT.gROOT.SetBatch(args.batch_mode)

      # call the function and do stuff
      args.func(args)

      if not args.debug:
        ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")

  except Exception, e:
    # stop redirecting if we crash as well
    if not args.debug:
      ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")

    logger.exception("{0}\nAn exception was caught!".format("-"*20))
