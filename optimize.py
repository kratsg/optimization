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

'''
  with tempfile.NamedTemporaryFile() as tmpFile:
    if not args.root_verbose:
      ROOT.gSystem.RedirectOutput(tmpFile.name, "w")

    # execute code here

    if not args.root_verbose:
      ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")
'''

# Set up ROOT
import ROOT


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

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process ROOT ntuples and Optimize Cuts.', usage='%(prog)s filename [filename] [options]')
  # positional argument, require the first argument to be the input filename
  parser.add_argument('--signal',
                      required=True,
                      type=str,
                      nargs='+',
                      help='signal ntuples')
  parser.add_argument('--bckgd',
                      required=True,
                      type=str,
                      nargs='+',
                      help='background ntuples')
  # these are options allowing for various additional configurations in filtering container and types to dump
  parser.add_argument('--tree',
                      type=str,
                      required=False,
                      dest='tree_name',
                      help='Specify the tree that contains the StoreGate structure. Default: CollectionTree',
                      default='oTree')

  '''general arguments for verbosity'''
  parser.add_argument('-v',
                      '--verbose',
                      dest='verbose',
                      action='count',
                      default=0,
                      help='Enable verbose output of various levels. Use --debug-root to enable ROOT debugging. Default: no verbosity')
  parser.add_argument('--debug-root',
                      dest='root_verbose',
                      action='store_true',
                      help='Enable ROOT debugging/output. Default: disabled')
  parser.add_argument('-b',
                      '--batch',
                      dest='batch_mode',
                      action='store_true',
                      help='Enable batch mode for ROOT. Default: disabled')

  parser.add_argument('-i',
                      '--interactive',
                      dest='interactive',
                      action='store_true',
                      help='(INACTIVE) Flip on/off interactive mode allowing you to navigate through the container types and properties.')

  # parse the arguments, throw errors if missing any
  args = parser.parse_args()
  if args.property_name_regex != '*' or args.attribute_name_regex != '*' or args.interactive:
    parser.error("The following arguments have not been implemented yet: --filterProps, --filterAttrs, --interactive. Sorry for the inconvenience.")

  try:
    # start execution of actual program
    import timing

    # set verbosity for python printing
    if args.verbose < 5:
      logger.setLevel(25 - args.verbose*5)
    else:
      logger.setLevel(logging.NOTSET + 1)

    with tempfile.NamedTemporaryFile() as tmpFile:
      if not args.root_verbose:
        ROOT.gSystem.RedirectOutput(tmpFile.name, "w")

      # if flag is shown, set batch_mode to true, else false
      ROOT.gROOT.SetBatch(args.batch_mode)

      # start by making a TChain
      logger.info("Initializing TChain")
      t = ROOT.TChain(args.tree_name)
      for fname in args.input_filename:
        if not os.path.isfile(fname):
          raise ValueError('The supplied input file `{0}` does not exist or I cannot find it.'.format(fname))
        else:
          logger.info("\tAdding {0}".format(fname))
          t.Add(fname)

      # Print some information
      logger.info('Number of input events: %s' % t.GetEntries())

      import pdb; pdb.set_trace();

      logger.log(25, "All done!")

      if not args.root_verbose:
        ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")

  except Exception, e:
    # stop redirecting if we crash as well
    if not args.root_verbose:
      ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")

    logger.exception("{0}\nAn exception was caught!".format("-"*20))
