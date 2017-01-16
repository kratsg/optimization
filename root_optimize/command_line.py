#!/usr/bin/env python
# -*- coding: utf-8 -*-,
# @file:    command_line.py
# @purpose: The entry point for root_optimize
# @author:  Giordon Stark <gstark@cern.ch>
# @date:    Dec 2016
#

# __future__ imports must occur at beginning of file
# redirect python output using the newer print function with file description
#   print(string, f=fd)
from __future__ import print_function
from __future__ import absolute_import

import os, sys
# grab the stdout and have python write to this instead
# ROOT will write to the original stdout
STDOUT = os.fdopen(os.dup(sys.stdout.fileno()), 'w')

# for logging, set it up
import logging
root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler(STDOUT))
logger = logging.getLogger("root_optimize.main")

# import all libraries
import argparse
import subprocess
import json
import hashlib
import copy
import operator
import glob
from collections import defaultdict

# root_optimize
from . import utils
from .json import NoIndent, NoIndentEncoder

# parallelization (http://blog.dominodatalab.com/simple-parallelization/)
from joblib import Parallel, delayed, load, dump
import multiprocessing

#@echo(write=logger.debug)
def do_cuts(args):
  from root_optimize.timing import secondsToStr

  # before doing anything, let's ensure the directory we make is ok
  if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
  else:
    raise IOError("Output directory already exists: {0:s}".format(args.output_directory))

  # first step is to group by the sample DID
  dids = defaultdict(list)
  for fname in args.files:
    dids[utils.get_did(fname)].append(fname)

  # load in the supercuts file
  supercuts = utils.read_supercuts_file(args.supercuts)

  # load up the weights file
  if not os.path.isfile(args.weightsFile):
    raise ValueError('The supplied weights file `{0}` does not exist or I cannot find it.'.format(args.weightsFile))
  else:
    weights = json.load(file(args.weightsFile))

  # parallelize
  num_cores = min(multiprocessing.cpu_count(), args.num_cores)
  logger.log(25, "Using {0} cores".format(num_cores) )
  results = Parallel(n_jobs=num_cores)(delayed(utils.do_cut)(did, files, supercuts, weights, args.tree_name, args.output_directory, args.eventWeightBranch, args.numpy) for did, files in dids.iteritems())

  for did, result in zip(dids, results):
    logger.log(25, 'DID {0:s}: {1:s}'.format(did, 'ok' if result[0] else 'not ok'))

  logger.log(25, "Total CPU elapsed time: {0}".format(secondsToStr(sum(result[1] for result in results))))

  return True

#@echo(write=logger.debug)
def do_optimize(args):

  # before doing anything, let's ensure the directory we make is ok
  if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
  else:
    raise IOError("Output directory already exists: {0:s}".format(args.output_directory))

  rescale = None
  did_to_group = None
  if args.rescale:
    rescale = json.load(file(args.rescale))
    if args.did_to_group is None: raise ValueError('If you are going to rescale, you need to pass in the --did-to-group mapping dict.')
    did_to_group = json.load(file(args.did_to_group))

  logger.log(25, 'Reading in all background files to calculate total background')

  total_bkgd = defaultdict(lambda: {'raw': 0., 'weighted': 0., 'scaled': 0.})
  bkgd_dids = []

  # make sure messages are only logged once, not multiple times
  duplicate_log_filter = utils.DuplicateFilter()
  logger.addFilter(duplicate_log_filter)

  # for each bkgd file, open, read, load, and combine
  for bkgd in args.bkgd:
    # expand out patterns if needed
    for fname in glob.glob(os.path.join(args.search_directory, bkgd)):
      did = utils.get_did(fname)
      logger.log(25, '\tLoading {0:s} ({1:s})'.format(did, fname))
      # generate a list of background dids
      bkgd_dids.append(did)
      with open(fname, 'r') as f:
        bkgd_data = json.load(f)
        for cuthash, counts_dict in bkgd_data.iteritems():
          for counts_type, counts in counts_dict.iteritems():
            total_bkgd[cuthash][counts_type] += counts
            if counts_type == 'scaled' and rescale:
              if did in rescale:
                scale_factor = rescale.get(did, 1.0)
                total_bkgd[cuthash][counts_type] *= scale_factor
                logger.log(25, '\t\tApplying scale factor for DID#{0:s}: {1:0.2f}'.format(did, scale_factor))
              if did_to_group[did] in rescale:
                scale_factor = rescale.get(did_to_group[did], 1.0)
                logger.log(25, '\t\tApplying scale factor for DID#{0:s} because it belongs in group "{1:s}": {2:0.2f}'.format(did, did_to_group[did], scale_factor))
                total_bkgd[cuthash][counts_type] *= scale_factor

  # remove the filter and clear up memory of stored logs
  logger.removeFilter(duplicate_log_filter)
  del duplicate_log_filter

  # create hash for background
  bkgdHash = hashlib.md5(str(sorted(bkgd_dids))).hexdigest()
  logger.log(25, "List of backgrounds produces hash: {0:s}".format(bkgdHash))
  # write the backgrounds to a file
  with open(os.path.join(args.output_directory, '{0:s}.json'.format(bkgdHash)), 'w+') as f:
    f.write(json.dumps(sorted(bkgd_dids)))

  logger.log(25, "Calculating significance for each signal file")
  # for each signal file, open, read, load, and divide with the current background
  for signal in args.signal:
    # expand out patterns if needed
    for fname in glob.glob(os.path.join(args.search_directory, signal)):
      did = utils.get_did(fname)
      logger.log(25, '\tCalculating significances for {0:s} ({1:s})'.format(did, fname))
      significances = []
      with open(fname, 'r') as f:
        signal_data = json.load(f)
        for cuthash, counts_dict in signal_data.iteritems():
          sig_dict = dict([('hash', cuthash)] + [('significance_{0:s}'.format(counts_type), utils.get_significance(args.lumi*1000*counts, args.lumi*1000*total_bkgd[cuthash][counts_type], args.insignificanceThreshold, args.bkgdUncertainty, args.bkgdStatUncertainty, total_bkgd[cuthash]['raw'])) for counts_type, counts in counts_dict.iteritems()] + [('yield_{0:s}'.format(counts_type), {'sig': args.lumi*1000*counts, 'bkg': args.lumi*1000*total_bkgd[cuthash][counts_type]}) for counts_type, counts in counts_dict.iteritems()])
          significances.append(sig_dict)
      logger.log(25, '\t\tCalculated significances for {0:d} cuts'.format(len(significances)))
      # at this point, we have a list of significances that we can dump to a file
      with open(os.path.join(args.output_directory, 's{0:s}.b{1:s}.json'.format(did, bkgdHash)), 'w+') as f:
        f.write(json.dumps(sorted(significances, key=operator.itemgetter('significance_scaled'), reverse=True)[:args.max_num_hashes], sort_keys=True, indent=4))

  return True

#@echo(write=logger.debug)
def do_generate(args):
  if os.path.isfile(args.output_filename):
    raise IOError("Output file already exists: {0}".format(args.output_filename))

  # this is a dict that holds the tree
  tree = utils.get_ttree(args.tree_name, [args.file], args.eventWeightBranch)

  # list of branches to loop over
  branches=[i.GetName() for i in tree.GetListOfBranches() if not i.GetName() == args.eventWeightBranch]

  supercuts = []

  for b in branches:
    if match_branch(b, args.skip_branches):
      logger.log(25, "{0:32s}:\tSkipping as requested".format(b))
      continue

    signal_direction = '>'

    if match_branch(b, args.fixed_branches):
      supercuts.append({'selections': "{0:s} > {{0}}".format(b),
                        'pivot': 0})
    else:
      supercuts.append({'selections': "{0:s} > {{0}}".format(b),
                        'st3': [NoIndent([0.0, 10.0, 1.0])]})

  with open(args.output_filename, 'w+') as f:
    f.write(json.dumps(sorted(supercuts, key=operator.itemgetter('selections')), sort_keys=True, indent=4, cls=NoIndentEncoder))

  return True

#@echo(write=logger.debug)
def do_hash(args):
  # first start by making the output directory
  if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
  else:
    raise IOError("Output directory already exists: {0}".format(args.output_directory))

  # next, read in the supercuts file
  data = utils.read_supercuts_file(args.supercuts)

  # either user provides a bunch of hashes, or we provide a summary.json file which contains the optimal cuts for us
  hash_values = args.hash_values
  if args.use_summary:
    logger.info("Treating hash_values as containing only a summary.json file instead")
    hash_values = set([r['hash'] for r in json.load(file(args.hash_values[0]))])

  logger.info("Finding cuts for {0:d} hashes.".format(len(hash_values)))
  # now loop over all cuts until we find all the hashes
  for cut in utils.get_cut(copy.deepcopy(data)):
    cut_hash = utils.get_cut_hash(cut)
    logger.info("\tChecking {0:s}".format(cut_hash))
    if cut_hash in hash_values:
      with open(os.path.join(args.output_directory, "{0}.json".format(cut_hash)), 'w+') as f:
        f.write(json.dumps([{k: (NoIndent(v) if k == 'pivot' else v)  for k, v in d.iteritems() if k in ['selections', 'pivot', 'fixed']} for d in cut], sort_keys=True, indent=4, cls=NoIndentEncoder))
      hash_values.remove(cut_hash)
      logger.log(25, "\tFound cut for hash {0:32s}. {1:d} hashes left.".format(cut_hash, len(hash_values)))
    if not hash_values: break
  # warn the user if there were hashes we could not decode for some reason
  if hash_values:
    logger.warning("There are inputs (hashes) provided we did not decode: {0}".format(hash_values))
  return True

#@echo(write=logger.debug)
def do_summary(args):
  # first check if output exists
  if os.path.exists(args.output): raise IOError("Output already exists: {0:s}".format(args.output))
  if not os.path.exists(args.mass_windows): raise IOError("Cannot find the mass_windows file: {0:s}".format(args.mass_windows))

  mass_windows = utils.load_mass_windows(args.mass_windows)
  num_cores = min(multiprocessing.cpu_count(),args.num_cores)
  logger.log(25, "Using {0} cores".format(num_cores) )
  results = Parallel(n_jobs=num_cores)(delayed(utils.get_summary)(filename, mass_windows, args.stop_masses) for filename in glob.glob(os.path.join(args.search_directory, "s*.b*.json")))
  results = filter(None, results)
  logger.log(25, "Generated summary for {0} items".format(len(results)))

  with open(args.output, 'w+') as f:
    f.write(json.dumps(sorted(results, key=operator.itemgetter('did')), sort_keys=True, indent=4))

  return True

def main():
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

  from . import __version__

  parser = argparse.ArgumentParser(add_help=False, description='Author: Giordon Stark. v{0}'.format(__version__),
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
                                   epilog='This is the top-level. You have no power here.')
  parser.add_argument('-h', '--help', action=_HelpAction, help='show this help message and exit')  # add custom help
  parser.add_argument('-a', '--allhelp', action=_AllHelpAction, help='show this help message and all subcommand help messages and exit')  # add custom help

  ''' subparsers have common parameters '''
  main_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  files_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  tree_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  supercuts_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  parallel_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  rescale_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  did_to_group_parser = argparse.ArgumentParser(add_help=False, formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))

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

  parallel_parser.add_argument('--ncores', type=int, required=False, dest='num_cores', metavar='<n>', help='Number of cores to use for parallelization. Defaults to max.', default=multiprocessing.cpu_count())

  rescale_parser.add_argument('--rescale', required=False, type=str, dest='rescale', metavar='<file.json>', help='json dict of groups and dids to apply a scale factor to. If not provided, no scaling will be done.', default=None)

  did_to_group_parser.add_argument('--did-to-group', required=False, type=str, dest='did_to_group', metavar='<file.json>', help='json dict mapping a did to a group.', default=None)

  ''' add subparsers '''
  subparsers = parser.add_subparsers(dest='command', help='actions available')

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

  # needs: files, tree, eventWeight, supercuts, parallel
  cuts_parser = subparsers.add_parser("cut", parents=[main_parser, files_parser, tree_parser, supercuts_parser, parallel_parser],
                                      description='Process ROOT ntuples and apply cuts. v.{0}'.format(__version__),
                                      usage='%(prog)s <file.root> ... [options]', help='Apply the cuts',
                                      formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                      epilog='cut will take in a series of files and calculate the unscaled and scaled counts for all cuts possible.')
  cuts_parser.add_argument('--weightsFile', type=str, required=False, dest='weightsFile', metavar='<weights file>', help='json file containing weights by DID', default='weights.json')
  cuts_parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<directory>', help='output directory to store the <hash>.json files', default='cuts')
  cuts_parser.add_argument('--numpy', required=False, action='store_true', help='Enable numpy optimization to speed up the cuts processing')


  # needs: signal, bkgd, bkgdUncertainty, insignificanceThreshold, tree, eventWeight
  optimize_parser = subparsers.add_parser("optimize", parents=[main_parser, rescale_parser, did_to_group_parser],
                                          description='Process ROOT ntuples and Optimize Cuts. v.{0}'.format(__version__),
                                          usage='%(prog)s  --signal={DID1}.json {DID2}.json [..] --bkgd={DID3}.json {DID4}.json {DID5}.json [...] [options]', help='Calculate significances for a series of computed cuts',
                                          formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                          epilog='optimize will take in numerous signal, background and calculate the significances for each signal and combine backgrounds automatically.')
  optimize_parser.add_argument('--signal', required=True, type=str, nargs='+', metavar='{DID}.json', help='ROOT files containing the signal cuts')
  optimize_parser.add_argument('--bkgd', required=True, type=str, nargs='+', metavar='{DID}.json', help='ROOT files containing the background cuts')
  optimize_parser.add_argument('--searchDirectory', required=False, type=str, dest='search_directory', help='Directory that contains all the {DID}.json files.', default='cuts')
  optimize_parser.add_argument('--bkgdUncertainty', type=float, required=False, dest='bkgdUncertainty', metavar='<sigma>', help='background uncertainty for calculating significance', default=0.3)
  optimize_parser.add_argument('--bkgdStatUncertainty', type=float, required=False, dest='bkgdStatUncertainty', metavar='<sigma>', help='background statistical uncertainty for calculating significance', default=0.3)
  optimize_parser.add_argument('--insignificance', type=float, required=False, dest='insignificanceThreshold', metavar='<min events>', help='minimum number of signal events for calculating significance', default=0.5)
  optimize_parser.add_argument('--lumi', type=float, required=False, dest='lumi', metavar='<scaled lumi>', help='Apply a global luminosity factor (units are ifb)', default=1.0)
  optimize_parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<directory>', help='output directory to store the <hash>.json files', default='significances')
  optimize_parser.add_argument('-n', '--max-num-hashes', required=False, type=int, metavar='<n>', help='Maximum number of hashes to print for each significance file', default=25)

  # needs: supercuts
  hash_parser = subparsers.add_parser("hash", parents=[main_parser, supercuts_parser],
                                      description='Given a hash from optimization, dump the cuts associated with it. v.{0}'.format(__version__),
                                      usage='%(prog)s <hash> [<hash> ...] [options]', help='Translate hash to cut',
                                      formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                      epilog='hash will take in a list of hashes and dump the cuts associated with them')
  hash_parser.add_argument('hash_values', type=str, nargs='+', metavar='<hash>', help='Specify a hash to look up the cut for. If --use-summary is flagged, you can pass in a summary.json file instead.')
  hash_parser.add_argument('-o', '--output', required=False, type=str, dest='output_directory', metavar='<directory>', help='output directory to store the <hash>.json files', default='outputHash')
  hash_parser.add_argument('--use-summary', action='store_true', help='If flagged, read in the list of hashes from the provided summary.json file')

  summary_parser = subparsers.add_parser("summary", parents=[main_parser, parallel_parser],
                                         description='Given the results of optimize (significances), generate a table of results for each mass point. v.{0}'.format(__version__),
                                         usage='%(prog)s --searchDirectory significances/ --massWindows massWindows.txt [options]', help='Summarize Optimization Results',
                                         formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
                                         epilog='summary will take in significances and summarize in a json file')
  summary_parser.add_argument('--searchDirectory', required=True, type=str, dest='search_directory', help='Directory that contains the significances')
  summary_parser.add_argument('--massWindows', required=True, type=str, dest='mass_windows', help='File that maps DID to mass')
  summary_parser.add_argument('--output', required=False, type=str, dest='output', help='Output json to make', default='summary.json')
  summary_parser.add_argument('--stop-masses', required=False, type=int, nargs='+', help='Allowed stop masses', default=[5000])

  # set the functions that get called with the given arguments
  cuts_parser.set_defaults(func=do_cuts)
  optimize_parser.set_defaults(func=do_optimize)
  generate_parser.set_defaults(func=do_generate)
  hash_parser.set_defaults(func=do_hash)
  summary_parser.set_defaults(func=do_summary)

  # print the help if called with no arguments
  import sys
  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
  # parse the arguments, throw errors if missing any
  args = parser.parse_args()

  try:
    # start execution of actual program
    from root_optimize import timing

    # set verbosity for python printing
    if args.verbose < 5:
      logger.setLevel(25 - args.verbose*5)
    else:
      logger.setLevel(logging.NOTSET + 1)

    # Set up ROOT
    import ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    # used to redirect ROOT output
    #   see http://stackoverflow.com/questions/21541238/get-ipython-doesnt-work-in-a-startup-script-for-ipython-ipython-notebook
    import tempfile

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

if __name__ == "__main__":
  main()
