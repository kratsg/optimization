#!/usr/bin/env python
# -*- coding: utf-8 -*-,
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
import glob
from collections import defaultdict

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
def apply_selection(tree, cut, eventWeightBranch):
  # use a global canvas
  global canvas
  selection = cut_to_selection(cut)
  # draw with selection
  tree.Draw(eventWeightBranch, '{0:s}*{1:s}'.format(eventWeightBranch, selection))
  # raw and weighted counts
  rawCount = 0
  weightedCount = 0
  # get drawn histogram
  if 'htemp' in canvas:
    htemp = canvas.GetPrimitive('htemp')
    rawCount = htemp.GetEntries()
    weightedCount = htemp.Integral()
  canvas.Clear()
  return rawCount, weightedCount

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
def apply_cuts(tree, cuts, eventWeightBranch, doNumpy=False):
  if doNumpy:
    # here, the tree is an rnp.tree2array() np.array
    events = tree[eventWeightBranch][reduce(np.bitwise_and, (apply_cut(tree[cut['branch']], cut.get('pivot', None), cut.get('signal_direction', None)) for cut in cuts))]
    return float(events.size), np.sum(events).astype(float)
  else:
    # here, the tree is a ROOT.TTree
    return apply_selection(tree, cuts, eventWeightBranch)

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
def get_did(filename):
  did_regex = re.compile('\.(\d{6,8})\.')
  m = did_regex.search(filename)
  if m is None: raise ValueError('Can\'t figure out the DID!')
  return m.group(1)

#@echo(write=logger.debug)
def get_scaleFactor(weights, did):
  weight = weights.get(did, None)
  if weight is None:
    raise KeyError("Could not find the weights for did=%s" % did)
  scaleFactor = 1.0
  cutflow = weight.get('num events')
  if cutflow == 0:
    raise ValueError('Num events = 0!')
  scaleFactor /= cutflow
  logger.log(25, "___________________________________________________________________")
  logger.log(25, " {0:8s} Type of Scaling Applied       |        Scale Factor      ".format(did))
  logger.log(25, "========================================|==========================")
  logger.log(25,"Cutflow:           {0:20.10f} | {0:0.10f}".format(cutflow, scaleFactor))
  scaleFactor *= weight.get('cross section')
  logger.log(25,"Cross Section:     {0:20.10f} | {0:0.10f}".format(weight.get('cross section'), scaleFactor))
  scaleFactor *= weight.get('filter efficiency')
  logger.log(25,"Filter Efficiency: {0:20.10f} | {0:0.10f}".format(weight.get('filter efficiency'), scaleFactor))
  scaleFactor *= weight.get('k-factor')
  logger.log(25,"k-factor:          {0:20.10f} | {0:0.10f}".format(weight.get('k-factor'), scaleFactor))
  scaleFactor *= weights.get('global_luminosity') * 1000 #to account for units on luminosity
  logger.log(25,"lumi:              {0:20.10f} | {0:0.10f}".format(weights.get('global_luminosity'), scaleFactor))
  logger.log(25, "‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
  return scaleFactor

#@echo(write=logger.debug)
def get_significance(signal, bkgd, insignificanceThreshold, bkgdUncertainty, bkgdStatUncertainty):
  # if not enough events, return string of which one did not have enough
  if signal < insignificanceThreshold:
    #sigDetails['insignificance'] = "signal"
    sig = -1
  elif bkgd < 1/(pow(bkgdStatUncertainty,2)): #require sqrt(numBkgd)/numBkgd < bkgdStatUncertainty
    #sigDetails['insignificance'] = "bkgd"
    sig = -2
  else:
    # otherwise, calculate!
    sig = ROOT.RooStats.NumberCountingUtils.BinomialExpZ(scaledSignal, scaledBkgd, bkgdUncertainty)
  return sig

#@echo(write=logger.debug)
def get_ttree(tree_name, filenames, eventWeightBranch):
  # this is a dict that holds the tree

  logger.info("Initializing TChain: {0}".format(tree_name))
  # start by making a TChain
  tree = ROOT.TChain(tree_name)
  for fname in filenames:
    if not os.path.isfile(fname):
      raise ValueError('The supplied input file `{0}` does not exist or I cannot find it.'.format(fname))
    else:
      logger.info("\tAdding {0}".format(fname))
      tree.Add(fname)

    # Print some information
    logger.info('\tNumber of input events: %s' % tree.GetEntries())

  # make sure the branches are compatible between the two
  branches = set(i.GetName() for i in tree.GetListOfBranches())

  if not eventWeightBranch in branches:
    raise ValueError('The event weight branch does not exist: {0}'.format(eventWeightBranch))

  return tree

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
def cut_to_selection(cut):
  return "*".join(["({0:s}{1:s}{2:0.2f})".format(c['branch'], c['signal_direction'], c['pivot']) for c in cut])

#@echo(write=logger.debug)
def do_cuts(args):
  # make the canvas global
  global canvas

  # before doing anything, let's ensure the directory we make is ok
  if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
  else:
    raise IOError("Output directory already exists: {0:s}".format(args.output_directory))

  # first step is to group by the sample DID
  dids = defaultdict(list)
  for fname in args.files:
    dids[get_did(fname)].append(fname)

  # load in the supercuts file
  supercuts = read_supercuts_file(args.supercuts)

  # build the containing canvas for all histograms drawn in `apply_selection`
  canvas = ROOT.TCanvas('test', 'test', 200, 10, 100, 100)

  # load up the weights file
  if not os.path.isfile(args.weightsFile):
    raise ValueError('The supplied weights file `{0}` does not exist or I cannot find it.'.format(args.weightsFile))
  else:
    weights = yaml.load(file(args.weightsFile))

  for did, files in dids.iteritems():
    try:
      # load up the tree for the files
      tree = get_ttree(args.tree_name, files, args.eventWeightBranch)
      # if using numpy optimization, load the tree as a numpy array to apply_cuts on
      if args.numpy:
        tree = rnp.tree2array(tree, branches=[args.eventWeightBranch]+[i['branch'] for i in supercuts])

      # get the scale factor
      sample_scaleFactor = get_scaleFactor(weights, did)

      # iterate over the cuts available
      cuts = {}
      for cut in get_cut(copy.deepcopy(supercuts)):
        cut_hash = get_cut_hash(cut)
        rawEvents, weightedEvents = apply_cuts(tree, cut, args.eventWeightBranch, args.numpy)
        scaledEvents = weightedEvents*sample_scaleFactor
        cuts[cut_hash] = {'raw': rawEvents, 'weighted': weightedEvents, 'scaled': scaledEvents}
      logger.log(25, "Applied {0:d} cuts".format(len(cuts)))
      with open('{0:s}/{1:s}.json'.format(args.output_directory, did), 'w+') as f:
        f.write(json.dumps(cuts, sort_keys=True, indent=4))
    except:
      logger.exception("Caught an error - skipping {0:s}".format(did))
      continue

  return True

#@echo(write=logger.debug)
def do_optimize(args):

  logger.log(25, 'Reading in all background files to calculate total background')

  total_bkgd = defaultdict(lambda: {'raw': 0., 'weighted': 0., 'scaled': 0.})
  bkgd_dids = []
  # for each bkgd file, open, read, load, and combine
  for bkgd in args.bkgd:
    # expand out patterns if needed
    for fname in glob.glob(os.path.join(args.search_directory, bkgd)):
      did = get_did(fname)
      logger.log(25, '\tLoading {0:s} ({1:s})'.format(did, fname))
      # generate a list of background dids
      bkgd_dids.append(did)
      with open(fname, 'r') as f:
        bkgd_data = json.load(f)
        for cuthash, counts_dict in bkgd_data.iteritems():
          for counts_type, counts in counts_dict.iteritems():
            total_bkgd[cuthash][counts_type] += counts

  logger.log(25, "Calculating significance for each signal file")

  # for each signal file, open, read, load, and divide with the current background
  for signal in args.signal:
    # expand out patterns if needed
    for fname in glob.glob(os.path.join(args.search_directory, signal)):
      did = get_did(fname)
      logger.log(25, '\tCalculating significances for {0:s} ({1:s})'.format(did, fname))
      significances = []
      with open(fname, 'r') as f:
        signal_data = json.load(f)
        for cuthash, counts_dict in signal_data.iteritems():
          sig_dict = [('hash', cuthash)] + [('significance_{0:s}'.format(counts_type), get_significance(counts, total_bkgd[cuthash][counts_type], args.insignificanceThreshold, args.bkgdUncertainty, args.bkgdStatUncertainty)) for counts_type, counts in counts_dict.iteritems()]
          significances.append(sig_dict)
      logger.log(25, '\t\tCalculated significances for {0:d} cuts'.format(len(significances)))
      # at this point, we have a list of significances that we can dump to a file
      with open('significances/s{0:s}.b{1:s}.json'.format(did, '-'.join(sorted(bkgd_dids))), 'w+'):
        f.write(json.dumps(sorted(significances, key=operator.itemgetter('significance_scaled'), reverse=True), sort_keys=True, indent=4))

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

  # this is a dict that holds the tree
  tree = get_ttree(args.tree_name, [args.file], args.eventWeightBranch)

  # list of branches to loop over
  branches=[i.GetName() for i in tree.GetListOfBranches() if not i.GetName() == args.eventWeightBranch]

  supercuts = []

  for b in branches:
    if match_branch(b, args.skip_branches):
      logger.log(25, "{0:32s}:\tSkipping as requested".format(b))
      continue

    signal_direction = '>'

    if match_branch(b, args.fixed_branches):
      supercuts.append({'branch': b,
                        'pivot': 0,
                        'signal_direction': signal_direction})
    else:
      supercuts.append({'branch': b,
                        'start': 0,
                        'stop': 10.0,
                        'step': 1.0,
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
                                   epilog='This is the top-level. You have no power here.')
  parser.add_argument('-h', '--help', action=_HelpAction, help='show this help message and exit')  # add custom help
  parser.add_argument('-a', '--allhelp', action=_AllHelpAction, help='show this help message and all subcommand help messages and exit')  # add custom help

  ''' subparsers have common parameters '''
  main_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  files_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  tree_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  supercuts_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))

  # general arguments for all
  main_parser.add_argument('-v','--verbose', dest='verbose', action='count', default=0, help='Enable verbose output of various levels. Use --debug to enable output for debugging.')
  main_parser.add_argument('--debug', dest='debug', action='store_true', help='Enable ROOT output and full-on debugging. Use this if you need to debug the application.')
  main_parser.add_argument('-b', '--batch', dest='batch_mode', action='store_true', help='Enable batch mode for ROOT.')
  # positional argument, require the first argument to be the input filename (hence adding the argument group)
  requiredNamed_files = files_parser.add_argument_group('required named arguments')
  requiredNamed_files.add_argument('files', type=str, nargs='+', metavar='<file.root>', help='ROOT files containing the optimization ntuples')

  # these are options for anything that needs to use the supercuts file
  supercuts_parser.add_argument('--supercuts', required=False, type=str, dest='supercuts', metavar='<file.json>', help='json dict of supercuts to generate optimization cuts to apply', default='supercuts.json')
  # these are options allowing for various additional configurations in filtering container and types to dump in the trees
  tree_parser.add_argument('--tree', type=str, required=False, dest='tree_name', metavar='<tree name>', help='name of the tree containing the ntuples', default='oTree')
  tree_parser.add_argument('--eventWeight', type=str, required=False, dest='eventWeightBranch', metavar='<branch name>', help='name of event weight branch in the ntuples. It must exist.', default='event_weight')

  ''' add subparsers '''
  subparsers = parser.add_subparsers(dest='command', help='actions available')
  # needs: files, tree, eventWeight, supercuts
  cuts_parser = subparsers.add_parser("cut", parents=[main_parser, files_parser, tree_parser, supercuts_parser],
                                      description='Process ROOT ntuples and apply cuts. v.{0}'.format(__version__),
                                      usage='%(prog)s <file.root> ... [options]', help='Apply the cuts',
                                      formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                      epilog='cut will take in a series of files and calculate the unscaled and scaled counts for all cuts possible.')
  cuts_parser.add_argument('--weightsFile', type=str, required=False, dest='weightsFile', metavar='<weights file>', help='yml file containing weights by DID', default='weights.yml')
  cuts_parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<directory>', help='output directory to store the <hash>.json files', default='cuts')
  cuts_parser.add_argument('--numpy', required=False, action='store_true', help='Enable numpy optimization to speed up the cuts processing')


  # needs: signal, bkgd, bkgdUncertainty, insignificanceThreshold, tree, eventWeight
  optimize_parser = subparsers.add_parser("optimize", parents=[main_parser],
                                          description='Process ROOT ntuples and Optimize Cuts. v.{0}'.format(__version__),
                                          usage='%(prog)s  --signal={DID1}.json {DID2}.json [..] --bkgd={DID3}.json {DID4}.json {DID5}.json [...] [options]', help='Calculate significances for a series of computed cuts',
                                          formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                          epilog='optimize will take in numerous signal, background and calculate the significances for each signal and combine backgrounds automatically.')
  optimize_parser.add_argument('--signal', required=True, type=str, nargs='+', metavar='{DID}.json', help='ROOT files containing the signal cuts')
  optimize_parser.add_argument('--bkgd', required=True, type=str, nargs='+', metavar='{DID}.json', help='ROOT files containing the background cuts')
  optimize_parser.add_argument('--searchDirectory', required=False, type=str, dest='search_directory', help='Directory that contains all the {DID}.json files.', default='cuts')
  optimize_parser.add_argument('--bkgdUncertainty', type=float, required=False, dest='bkgdUncertainty', metavar='<sigma>', help='background uncertainty for calculating significance', default=0.3)
  optimize_parser.add_argument('--bkgdStatUncertainty', type=float, required=False, dest='bkgdStatUncertainty', metavar='<sigma>', help='background statistical uncertainty for calculating significance', default=0.3)
  optimize_parser.add_argument('--insignificance', type=int, required=False, dest='insignificanceThreshold', metavar='<min events>', help='minimum number of signal events for calculating significance', default=2)

  # needs: files, tree, eventWeight
  generate_parser = subparsers.add_parser("generate", parents=[main_parser, tree_parser],
                                          description='Given the ROOT ntuples, generate a supercuts.json template. v.{0}'.format(__version__),
                                          usage='%(prog)s <file.root> ... [options]', help='Write supercuts template',
                                          formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                          epilog='generate will take in signal, background and generate the supercuts template file for you to edit and use (rather than making it by hand)')
  generate_parser.add_argument('file', type=str, help='A single file that contains the general structure of the optimization tree on which to generate a supercuts file from.')
  generate_parser.add_argument('-o', '--output', required=False, type=str, dest='output_filename', metavar='<file.json>', help='output json file to store the generated supercuts template', default='supercuts.json')
  generate_parser.add_argument('--fixedBranches', type=str, nargs='+', required=False, dest='fixed_branches', metavar='<branch>', help='branches that should have a fixed cut. can use wildcards', default=[])
  generate_parser.add_argument('--skipBranches', type=str, nargs='+', required=False, dest='skip_branches', metavar='<branch>', help='branches that should be skipped. can use wildcards', default=[])

  # needs: supercuts
  hash_parser = subparsers.add_parser("hash", parents=[main_parser, supercuts_parser],
                                      description='Given a hash from optimization, dump the cuts associated with it. v.{0}'.format(__version__),
                                      usage='%(prog)s <hash> [<hash> ...] [options]', help='Translate hash to cut',
                                      formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                      epilog='hash will take in a list of hashes and dump the cuts associated with them')
  hash_parser.add_argument('hash_values', type=str, nargs='+', metavar='<hash>', help='Specify a hash to look up the cut for')
  hash_parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<directory>', help='output directory to store the <hash>.json files', default='outputHash')

  # set the functions that get called with the given arguments
  cuts_parser.set_defaults(func=do_cuts)
  optimize_parser.set_defaults(func=do_optimize)
  generate_parser.set_defaults(func=do_generate)
  hash_parser.set_defaults(func=do_hash)

  # print the help if called with no arguments
  import sys
  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
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
