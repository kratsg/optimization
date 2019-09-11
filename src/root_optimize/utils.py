#!/usr/bin/env python
# -*- coding: utf-8 -*-,
from __future__ import absolute_import
from __future__ import print_function

import csv
import copy
import re
import json
import fnmatch
import hashlib
import itertools
import numpy as np
import numexpr as ne
import scipy.special
import os
import sys
from time import clock
from tqdm import tqdm
import contextlib
import formulate
import uproot
from collections import defaultdict

try:
    from functools import reduce
except:
    pass

import logging

logger = logging.getLogger(__name__)


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
        argdefs = dict(zip(argnames[-len(fn_defaults) :], fn_defaults))

        def wrapped(*v, **k):
            # Collect function arguments by chaining together positional,
            # defaulted, extra positional and keyword arguments.
            positional = map(format_arg_value, zip(argnames, v))
            defaulted = [
                format_arg_value((a, argdefs[a]))
                for a in argnames[len(v) :]
                if a not in k
            ]
            nameless = map(repr, v[argcount:])
            keyword = map(format_arg_value, k.items())
            args = positional + defaulted + nameless + keyword
            write("%s(%s)\n" % (fn.__name__, ", ".join(args)))
            return fn(*v, **k)

        return wrapped

    write = echokwargs.get("write", sys.stdout.write)
    if len(echoargs) == 1 and callable(echoargs[0]):
        return echo_wrap(echoargs[0])
    return echo_wrap


# http://stackoverflow.com/a/31953563/1532974
# Do not allow duplicate log messages, such as inside loops
class DuplicateFilter(object):
    def __init__(self):
        self.msgs = set()

    def filter(self, record):
        rv = record.msg not in self.msgs
        self.msgs.add(record.msg)
        return rv


# http://stackoverflow.com/a/38739634/1532974
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super(self.__class__, self).__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


# for redirecting sys.stdout to tqdm
class DummyTqdmFile(object):
    """Dummy file-like that will write to tqdm"""

    file = None

    def __init__(self, file):
        self.file = file

    def write(self, x):
        # Avoid print() second call (useless \n)
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self.file)

    def flush(self):
        pass


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


# @echo(write=logger.debug)
def load_mass_windows(filename):
    with open(filename, "r") as f:
        return {l[0]: tuple(l[1:4]) for l in csv.reader(f, delimiter="\t")}


# @echo(write=logger.debug)
did_regex = re.compile("(?:00)?([1-9]\d{5})(?=\.[a-zA-Z_]+\.?)")


def get_did(filename):
    global did_regex
    # check if the dirname matches
    m = did_regex.search(os.path.basename(os.path.dirname(filename)))
    if m is None:
        # no, does the basename match?
        m = did_regex.search(os.path.basename(filename))
        if m is None:
            # no, we have no idea what this shit is, use the basename of the filename
            logger.warning(
                "Can't figure out DID from dirname: {0:s}! Using the input basename instead: {1:s}".format(
                    os.path.basename(os.path.dirname(filename)),
                    os.path.basename(filename),
                )
            )
            return os.path.basename(filename)
    return m.group(1)


# @echo(write=logger.debug)
def match_branch(branch, list_of_branches):
    if branch in list_of_branches:
        return True
    for b in list_of_branches:
        if re.compile(fnmatch.translate(b)).search(branch):
            return True
    return False


# @echo(write=logger.debug)
def read_supercuts_file(filename):
    logger.info("Reading supercuts file {0}".format(filename))
    logger.info("\tOpening")
    with open(filename) as f:
        supercuts = json.load(f)

    logger.info("\tLoaded")
    selections = set([supercut["selections"] for supercut in supercuts])
    try:
        for supercut in supercuts:
            selections.remove(supercut["selections"])
    except KeyError:
        raise KeyError(
            "Found more than one supercut definition on {0}".format(
                supercut["selections"]
            )
        )

    logger.info("\tFound {1:d} supercut definitions".format(filename, len(supercuts)))
    return supercuts


# @echo(write=logger.debug)
def get_scaleFactor(weights, did):
    weight = weights.get(did, None)
    if weight is None:
        logger.warning("Could not find the weights for did=%s" % did)
        return 1.0
    scaleFactor = 1.0
    cutflow = weight.get("num events")
    if cutflow == 0:
        raise ValueError("Num events = 0!")
    scaleFactor /= cutflow
    logger.info("___________________________________________________________________")
    logger.info(
        " {0:8s} Type of Scaling Applied       |        Scale Factor      ".format(did)
    )
    logger.info("========================================|==========================")
    logger.info(
        "Cutflow:           {0:20.10f} | {1:0.10f}".format(cutflow, scaleFactor)
    )
    scaleFactor *= weight.get("cross section")
    logger.info(
        "Cross Section:     {0:20.10f} | {1:0.10f}".format(
            weight.get("cross section"), scaleFactor
        )
    )
    scaleFactor *= weight.get("filter efficiency")
    logger.info(
        "Filter Efficiency: {0:20.10f} | {1:0.10f}".format(
            weight.get("filter efficiency"), scaleFactor
        )
    )
    scaleFactor *= weight.get("k-factor")
    logger.info(
        "k-factor:          {0:20.10f} | {1:0.10f}".format(
            weight.get("k-factor"), scaleFactor
        )
    )
    logger.info("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
    return scaleFactor


def significance(signalExp, backgroundExp, relativeBkgUncert):
    """ Numpy/Scipy port of the RooStats function `BinomialExpZ'

    See: https://root.cern.ch/doc/master/NumberCountingUtils_8cxx_source.html
    """
    # pylint: disable=invalid-name
    mainInf = signalExp + backgroundExp
    tau = 1.0 / backgroundExp / (relativeBkgUncert * relativeBkgUncert)
    auxiliaryInf = backgroundExp * tau
    P_Bi = scipy.special.betainc(mainInf, auxiliaryInf + 1, 1.0 / (1.0 + tau))
    return -scipy.special.ndtri(P_Bi)


# @echo(write=logger.debug)
def get_significance(
    signal, bkgd, insignificanceThreshold, bkgdUncertainty, bkgdStatUncertainty, rawBkgd
):
    # if not enough events, return string of which one did not have enough
    if signal < insignificanceThreshold:
        # sigDetails['insignificance'] = "signal"
        sig = -1
    elif bkgd < insignificanceThreshold:
        # sigDetails['insignificance'] = "bkgd"
        sig = -2
    elif rawBkgd < 1 / (
        pow(bkgdStatUncertainty, 2)
    ):  # require sqrt(numBkgd)/numBkgd < bkgdStatUncertainty
        # sigDetails['insignificance'] = "bkgdstat"
        sig = -3
    else:
        # otherwise, calculate!
        sig = significance(signal, bkgd, bkgdUncertainty)
    return sig


# @echo(write=logger.debug)
def cut_to_selection(cut):
    return cut["selections"].format(*cut["pivot"])


# @echo(write=logger.debug)
def cuts_to_selection(cuts):
    return "({})".format(")*(".join(map(cut_to_selection, cuts)))


strformat_chars = re.compile("[{}]")
# @echo(write=logger.debug)
def selection_to_branches(selection_string):
    return formulate.from_auto(strformat_chars.sub('', selection_string)).variables


def supercuts_to_branches(supercuts):
    return set(
        itertools.chain.from_iterable(
            selection_to_branches(supercut["selections"]) for supercut in supercuts
        )
    )


# @echo(write=logger.debug)
def get_cut(superCuts, index=0):
    # reached bottom of iteration, yield what we've done
    if index >= len(superCuts):
        yield superCuts
    else:
        # start of iteration, make a copy of the input dictionary
        # if index == 0: superCuts = copy.deepcopy(superCuts)
        # reference to item
        item = superCuts[index]
        # are we doing a fixed cut? they should specify only pivot
        try:
            # if they don't want a fixed cut, then they need start, stop, step in st3
            for pivot in itertools.product(*(np.arange(*st3) for st3 in item["st3"])):
                # set the pivot value
                item["pivot"] = pivot
                item["fixed"] = False
                # recursively call, yield the result which is the superCuts
                for cut in get_cut(superCuts, index + 1):
                    yield cut
        except KeyError:
            item["fixed"] = True
            for cut in get_cut(superCuts, index + 1):
                yield cut


def get_n_cuts(supercuts):
    total = 1
    for supercut in supercuts:
        if "st3" in supercut:
            total *= reduce(
                lambda x, y: x * y,
                (np.ceil((st3[1] - st3[0]) / st3[2]) for st3 in supercut["st3"]),
            )
    return total


# @echo(write=logger.debug)
def get_cut_hash(cut):
    return hashlib.md5(
        str([sorted(obj.items()) for obj in cut]).encode("utf-8")
    ).hexdigest()


# @echo(write=logger.debug)
def apply_cut(arr, cut):
    return ne.evaluate(cut_to_selection(cut), local_dict=arr)


# @echo(write=logger.debug)
def apply_cuts(events, cuts, eventWeightBranch):
    entireSelection = "{0:s}*{1:s}".format(eventWeightBranch, cuts_to_selection(cuts))
    events = ne.evaluate(entireSelection, local_dict=events)
    # events = tree[eventWeightBranch][reduce(np.bitwise_and, (apply_cut(tree, cut) for cut in cuts))]
    # count number of events that pass, not summing the weights since `events!=0` returns a boolean array
    return np.sum(events != 0).astype(float), np.sum(events).astype(float)


# @echo(write=logger.debug)
def do_cut(
    tree_name, files, supercuts, weights, output_directory, eventWeightBranch, pids
):

    position = -1
    if pids is not None:
        # handle pid registration
        if os.getpid() not in pids:
            pids[np.argmax(pids == 0)] = os.getpid()
        # this gives us the position of this particular process in our list of processes
        position = np.where(pids == os.getpid())[0][0]

    start = clock()
    try:
        branchesSpecified = supercuts_to_branches(supercuts)
        eventWeightBranchesSpecified = selection_to_branches(eventWeightBranch)
        branches = list(
            itertools.chain(branchesSpecified, eventWeightBranchesSpecified)
        )

        missingBranches = False
        for fname in files:
            tree = uproot.open(fname)[tree_name]
            for branch in branches:
                if branch not in tree:
                    logger.error(
                        'branch {} not found in {} for {}'.format(
                            branch, tree_name, fname
                        )
                    )
                    missingBranches |= True
        if missingBranches:
            sys.exit(1)

        # iterate over the cuts available
        cuts = defaultdict(lambda: {'raw': 0, 'weighted': 0})

        events_tqdm = tqdm(
            total=uproot.numentries(files, tree_name),
            disable=(position == -1),
            position=2 * position + 1,
            leave=False,
            mininterval=5,
            maxinterval=10,
            unit="events",
            dynamic_ncols=True,
        )
        for file, start, stop, events in uproot.iterate(
            files,
            tree_name,
            branches=branches,
            namedecode='utf-8',
            reportfile=True,
            reportentries=True,
        ):
            import time, random

            time.sleep(0.2 * random.randrange(1, 5))
            events_tqdm.set_description(
                "({1:d}) Working on {0:s}".format(
                    tree_name.decode('utf-8'), 2 * position + 1
                )
            )
            for cut in tqdm(
                get_cut(copy.deepcopy(supercuts)),
                desc="({1:d}) Applying cuts to {0:s}".format(
                    file.name.decode('utf-8'), 2 * position + 2
                ),
                total=get_n_cuts(supercuts),
                disable=(position == -1),
                position=2 * position + 2,
                leave=False,
                unit="cuts",
                miniters=10,
                dynamic_ncols=True,
            ):
                cut_hash = get_cut_hash(cut)
                rawEvents, weightedEvents = apply_cuts(events, cut, eventWeightBranch)
                cuts[cut_hash]['raw'] += rawEvents
                cuts[cut_hash]['weighted'] += weightedEvents

            events_tqdm.update(stop - start)

        with open(
            "{0:s}/{1:s}.json".format(output_directory, tree_name.decode('utf-8')), "w+"
        ) as f:
            f.write(json.dumps(cuts, sort_keys=True, indent=4))
            result = True
    except:
        logger.exception(
            "Caught an error - skipping {0:s}".format(tree_name.decode('utf-8'))
        )
        result = False
    end = clock()
    return (result, end - start)


def get_summary(filename, mass_windows, stop_masses=[]):
    """ Primarily used from within do_summary
        - given a significance file, the mass windows, produce a summary dictionary for it
  """
    logger.info("\treading {0:s}".format(filename))
    with open(filename) as f:
        entry = json.load(f)[0]

        cut_hash = entry["hash"]
        significance = entry["significance_weighted"]
        signal_yield = entry["yield_weighted"]["sig"]
        bkgd_yield = entry["yield_weighted"]["bkg"]

        ratio = -1
        try:
            ratio = signal_yield / bkgd_yield
        except:
            pass

        did = get_did(os.path.basename(filename))

        m_gluino, m_stop, m_lsp = [
            int(item) for item in mass_windows.get(did, (0, 0, 0))
        ]
        if not m_stop in stop_masses:
            return {}

        return {
            "hash": cut_hash,
            "significance": significance,
            "signal": signal_yield,
            "bkgd": bkgd_yield,
            "ratio": ratio,
            "did": did,
            "m_gluino": int(m_gluino),
            "m_stop": int(m_stop),
            "m_lsp": int(m_lsp),
        }
