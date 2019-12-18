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

# for logging, set it up
import logging

logger = logging.getLogger(__name__)

# import all libraries
import argparse
import json
import copy
import operator
import glob
import os
from collections import defaultdict
import tempfile
import tqdm
import uproot
import re
import fnmatch
import itertools

# root_optimize
from . import utils
from .json import NoIndent, NoIndentEncoder

# parallelization (http://blog.dominodatalab.com/simple-parallelization/)
from joblib import Parallel, delayed
import multiprocessing

# @echo(write=logger.debug)
def do_cuts(args):
    from root_optimize.timing import secondsToStr

    # before doing anything, let's ensure the directory we make is ok
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)
    elif args.overwrite:
        import shutil

        shutil.rmtree(args.output_directory)
    else:
        raise IOError(
            "Output directory already exists: {0:s}".format(args.output_directory)
        )

    tree_patterns = [
        re.compile(str.encode(fnmatch.translate(tree_pattern)))
        for tree_pattern in args.tree_patterns
    ]

    # first step is to group by the tree name
    trees = defaultdict(list)
    for fname in args.files:
        with uproot.open(fname) as f:
            tree_names = set(
                sorted(
                    tname.split(b';')[0]
                    for tname in f.allkeys(
                        filterclass=lambda cls: issubclass(
                            cls, uproot.tree.TTreeMethods
                        )
                    )
                )
            )
            logger.log(25, "{0:s} has {1:d} trees".format(fname, len(tree_names)))
            for tree_name in tree_names:
                matched = any(
                    tree_pattern.search(tree_name) for tree_pattern in tree_patterns
                )
                if matched:
                    trees[tree_name].append(fname)
                logger.log(
                    25,
                    "  - [{1:s}] {0:s}".format(
                        tree_name.decode('utf-8'), "x" if matched else " "
                    ),
                )

    # load in the supercuts file
    supercuts = utils.read_supercuts_file(args.supercuts)

    branchesSpecified = utils.supercuts_to_branches(supercuts)
    eventWeightBranchesSpecified = utils.extract_branch_names(args.eventWeightBranch)
    proposedBranches = set(
        map(
            str.encode, itertools.chain(branchesSpecified, eventWeightBranchesSpecified)
        )
    )

    # parallelize
    num_cores = min(multiprocessing.cpu_count(), args.num_cores)
    logger.log(25, "Using {0} cores".format(num_cores))

    pids = None
    # if pids is None, do_cut() will disable the progress
    if not args.hide_subtasks:
        from numpy import memmap, uint64

        pids = memmap(
            os.path.join(tempfile.mkdtemp(), "pids"),
            dtype=uint64,
            shape=num_cores,
            mode="w+",
        )

    overall_progress = tqdm.tqdm(
        total=len(trees),
        desc="Num. trees",
        position=0,
        leave=True,
        unit="tree",
        ncols=120,
        miniters=1,
    )

    class BatchCompletionCallBack(object):
        completed = defaultdict(int)

        def __init__(self, time, index, parallel):
            self.index = index
            self.parallel = parallel

        def __call__(self, index):
            BatchCompletionCallBack.completed[self.parallel] += 1
            overall_progress.update()
            # overall_progress.refresh()
            if self.parallel._original_iterator is not None:
                self.parallel.dispatch_next()

    import joblib.parallel

    joblib.parallel.BatchCompletionCallBack = BatchCompletionCallBack

    with utils.std_out_err_redirect_tqdm():
        results = Parallel(n_jobs=num_cores)(
            delayed(utils.do_cut)(
                tree_name,
                files,
                supercuts,
                proposedBranches,
                args.output_directory,
                args.eventWeightBranch,
                pids,
            )
            for tree_name, files in trees.items()
        )

    overall_progress.close()

    for tree_name, result in zip(trees, results):
        logger.log(
            25,
            "Tree {0:s}: {1:s}".format(
                tree_name.decode('utf-8'), "ok" if result[0] else "not ok"
            ),
        )

    logger.log(
        25,
        "Total CPU elapsed time: {0}".format(
            secondsToStr(sum(result[1] for result in results))
        ),
    )

    return True


# @echo(write=logger.debug)
def do_optimize(args):

    # before doing anything, let's ensure the directory we make is ok
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)
    else:
        raise IOError(
            "Output directory already exists: {0:s}".format(args.output_directory)
        )

    logger.log(25, "Reading in all background files to calculate total background")

    total_bkgd = defaultdict(lambda: {"raw": 0.0, "weighted": 0.0})
    bkgd_files = []
    sig_files = []

    # for each bkgd file, open, read, load, and combine
    for bkgd in args.bkgd:
        # expand out patterns if needed
        for fname in glob.glob(os.path.join(args.search_directory, bkgd)):
            logger.log(25, "\tLoading {0:s}".format(fname))
            bkgd_files.append(os.path.basename(fname))
            with open(fname, "r") as f:
                bkgd_data = json.load(f)
                for cuthash, counts_dict in bkgd_data.items():
                    for counts_type, counts in counts_dict.items():
                        total_bkgd[cuthash][counts_type] += counts

    logger.log(25, "Calculating significance for each signal file")
    # for each signal file, open, read, load, and divide with the current background
    for signal in args.signal:
        # expand out patterns if needed
        for fname in glob.glob(os.path.join(args.search_directory, signal)):
            sig_files.append(os.path.basename(fname))
            logger.log(25, "\tCalculating significances for {0:s}".format(fname))
            significances = []
            with open(fname, "r") as f:
                signal_data = json.load(f)
                for cuthash, counts_dict in signal_data.items():
                    sig_dict = dict(
                        [("hash", cuthash)]
                        + [
                            (
                                "significance_{0:s}".format(counts_type),
                                utils.get_significance(
                                    counts,
                                    total_bkgd[cuthash][counts_type],
                                    args.insignificanceThreshold,
                                    args.bkgdUncertainty,
                                    args.bkgdStatUncertainty,
                                    total_bkgd[cuthash]["raw"],
                                ),
                            )
                            for counts_type, counts in counts_dict.items()
                        ]
                        + [
                            (
                                "yield_{0:s}".format(counts_type),
                                {
                                    "sig": counts,
                                    "bkg": total_bkgd[cuthash][counts_type],
                                },
                            )
                            for counts_type, counts in counts_dict.items()
                        ]
                    )
                    significances.append(sig_dict)
            logger.log(
                25,
                "\t\tCalculated significances for {0:d} cuts".format(
                    len(significances)
                ),
            )
            # at this point, we have a list of significances that we can dump to a file
            with open(
                os.path.join(
                    args.output_directory, "{0:s}".format(os.path.basename(fname))
                ),
                "w+",
            ) as f:
                f.write(
                    json.dumps(
                        sorted(
                            significances,
                            key=operator.itemgetter("significance_weighted"),
                            reverse=True,
                        )[: args.max_num_hashes],
                        sort_keys=True,
                        indent=4,
                    )
                )

        bkgd_files = sorted(bkgd_files)
        sig_files = sorted(sig_files)

        # write the files used to a file
        with open(os.path.join(args.output_directory, "config.json"), "w+") as f:
            f.write(
                json.dumps(
                    {'backgrounds': bkgd_files, 'signals': sig_files},
                    sort_keys=True,
                    indent=4,
                )
            )

    return True


# @echo(write=logger.debug)
def do_generate(args):
    if os.path.isfile(args.output_filename):
        raise IOError("Output file already exists: {0}".format(args.output_filename))

    if len(args.tree_patterns) > 1:
        raise ValueError("Must only specify one tree name.")

    # this is a dict that holds the tree
    tree = uproot.open(args.file)[args.tree_patterns[0]]

    supercuts = []

    for b in tree.keys():
        if utils.match_branch(b, args.skip_branches):
            logger.log(25, "{0:32s}:\tSkipping as requested".format(b))
            continue

        if utils.match_branch(b, args.fixed_branches):
            supercuts.append({"selections": "{0:s} > {{0}}".format(b), "pivot": 0})
        else:
            supercuts.append(
                {
                    "selections": "{0:s} > {{0}}".format(b.decode('utf-8')),
                    "st3": [NoIndent([0.0, 10.0, 1.0])],
                }
            )

    with open(args.output_filename, "w+") as f:
        f.write(
            json.dumps(
                sorted(supercuts, key=operator.itemgetter("selections")),
                sort_keys=True,
                indent=4,
                cls=NoIndentEncoder,
            )
        )

    return True


# @echo(write=logger.debug)
def do_hash(args):
    # first start by making the output directory
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)
    else:
        raise IOError(
            "Output directory already exists: {0}".format(args.output_directory)
        )

    # next, read in the supercuts file
    data = utils.read_supercuts_file(args.supercuts)

    # either user provides a bunch of hashes, or we provide a summary.json file which contains the optimal cuts for us
    hash_values = args.hash_values
    if args.use_summary:
        logger.info(
            "Treating hash_values as containing only a summary.json file instead"
        )
        hash_values = set([r["hash"] for r in json.load(open(args.hash_values[0]))])

    logger.info("Finding cuts for {0:d} hashes.".format(len(hash_values)))
    # now loop over all cuts until we find all the hashes
    for cut in utils.get_cut(copy.deepcopy(data)):
        cut_hash = utils.get_cut_hash(cut)
        logger.info("\tChecking {0:s}".format(cut_hash))
        if cut_hash in hash_values:
            with open(
                os.path.join(args.output_directory, "{0}.json".format(cut_hash)), "w+"
            ) as f:
                f.write(
                    json.dumps(
                        [
                            {
                                k: (
                                    NoIndent(tuple(map(float, v)))
                                    if k == "pivot"
                                    else v
                                )
                                for k, v in d.items()
                                if k in ["selections", "pivot", "fixed"]
                            }
                            for d in cut
                        ],
                        sort_keys=True,
                        indent=4,
                        cls=NoIndentEncoder,
                    )
                )
            hash_values.remove(cut_hash)
            logger.log(
                25,
                "\tFound cut for hash {0:32s}. {1:d} hashes left.".format(
                    cut_hash, len(hash_values)
                ),
            )
        if not hash_values:
            break
    # warn the user if there were hashes we could not decode for some reason
    if hash_values:
        logger.warning(
            "There are inputs (hashes) provided we did not decode: {0}".format(
                hash_values
            )
        )
    return True


# @echo(write=logger.debug)
def do_summary(args):
    # first check if output exists
    if os.path.exists(args.output):
        raise IOError("Output already exists: {0:s}".format(args.output))

    num_cores = min(multiprocessing.cpu_count(), args.num_cores)
    logger.log(25, "Using {0} cores".format(num_cores))

    config = json.load(open(os.path.join(args.search_directory, "config.json")))

    results = Parallel(n_jobs=num_cores)(
        delayed(utils.get_summary)(
            os.path.join(args.search_directory, filename),
            args.interpretation.split(":"),
            re.compile(args.fmtstr),
        )
        for filename in config['signals']
    )
    results = list(filter(None, results))
    logger.log(25, "Generated summary for {0} items".format(len(results)))

    with open(args.output, "w+") as f:
        f.write(
            json.dumps(
                sorted(results, key=operator.itemgetter("filename")),
                sort_keys=True,
                indent=4,
            )
        )

    return True


def rooptimize():
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
                action
                for action in parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ]
            # there will probably only be one subparser_action,
            # but better save than sorry
            for subparsers_action in subparsers_actions:
                # get all subparsers and print help
                for choice, subparser in subparsers_action.choices.items():
                    print("-" * 80)
                    print("Subparser '{}'".format(choice))
                    print(subparser.format_help())
            parser.exit()

    from .version import __version__

    parser = argparse.ArgumentParser(
        add_help=False,
        description="Author: Giordon Stark. v{0}".format(__version__),
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
        epilog="This is the top-level. You have no power here.",
    )
    parser.add_argument(
        "-h", "--help", action=_HelpAction, help="show this help message and exit"
    )  # add custom help
    parser.add_argument(
        "-a",
        "--allhelp",
        action=_AllHelpAction,
        help="show this help message and all subcommand help messages and exit",
    )  # add custom help

    """ subparsers have common parameters """
    main_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
    )
    files_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
    )
    tree_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
    )
    supercuts_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
    )
    parallel_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30),
    )

    # general arguments for all
    main_parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        default=0,
        help="Enable verbose output of various levels.",
    )
    # positional argument, require the first argument to be the input filename (hence adding the argument group)
    requiredNamed_files = files_parser.add_argument_group("required named arguments")
    requiredNamed_files.add_argument(
        "files", type=str, nargs="+", metavar="<file.root>", help="input ntuples"
    )

    # these are options for anything that needs to use the supercuts file
    supercuts_parser.add_argument(
        "--supercuts",
        required=False,
        type=str,
        dest="supercuts",
        metavar="<file.json>",
        help="json dict of supercuts to generate optimization cuts to apply",
        default="supercuts.json",
    )
    # these are options allowing for various additional configurations in filtering container and types to dump in the trees
    tree_parser.add_argument(
        "--tree-pattern",
        type=str,
        nargs="+",
        required=False,
        dest="tree_patterns",
        metavar="<tree pattern>",
        help="patterns to match against tree names in ntuples (default is all trees)",
        default="*",
    )
    tree_parser.add_argument(
        "--eventWeight",
        type=str,
        required=False,
        dest="eventWeightBranch",
        metavar="<branch name>",
        help="name of event weight branch in the ntuples. It must exist.",
        default="event_weight",
    )

    parallel_parser.add_argument(
        "--ncores",
        type=int,
        required=False,
        dest="num_cores",
        metavar="<n>",
        help="Number of cores to use for parallelization. Defaults to max.",
        default=multiprocessing.cpu_count(),
    )

    """ add subparsers """
    subparsers = parser.add_subparsers(dest="command", help="actions available")

    # needs: files, tree, eventWeight
    generate_parser = subparsers.add_parser(
        "generate",
        parents=[main_parser, tree_parser],
        description="Given the ROOT ntuples, generate a supercuts.json template. v.{0}".format(
            __version__
        ),
        usage="%(prog)s <file.root> ... [options]",
        help="Write supercuts template",
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
        epilog="generate will take in signal, background and generate the supercuts template file for you to edit and use (rather than making it by hand)",
    )
    generate_parser.add_argument(
        "file",
        type=str,
        help="A single file that contains the general structure of the optimization tree on which to generate a supercuts file from.",
    )
    generate_parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        dest="output_filename",
        metavar="<file.json>",
        help="output json file to store the generated supercuts template",
        default="supercuts.json",
    )
    generate_parser.add_argument(
        "--fixedBranches",
        type=str,
        nargs="+",
        required=False,
        dest="fixed_branches",
        metavar="<branch>",
        help="branches that should have a fixed cut. can use wildcards",
        default=[],
    )
    generate_parser.add_argument(
        "--skipBranches",
        type=str,
        nargs="+",
        required=False,
        dest="skip_branches",
        metavar="<branch>",
        help="branches that should be skipped. can use wildcards",
        default=[],
    )

    # needs: files, tree, eventWeight, supercuts, parallel
    cuts_parser = subparsers.add_parser(
        "cut",
        parents=[
            main_parser,
            files_parser,
            tree_parser,
            supercuts_parser,
            parallel_parser,
        ],
        description="Process ROOT ntuples and apply cuts. v.{0}".format(__version__),
        usage="%(prog)s <file.root> ... [options]",
        help="Apply the cuts",
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
        epilog="cut will take in a series of files and calculate the unweighted and weighted counts for all cuts possible.",
    )
    cuts_parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        dest="output_directory",
        metavar="<directory>",
        help="output directory to store the <hash>.json files",
        default="cuts",
    )
    cuts_parser.add_argument(
        "-f",
        "--overwrite",
        required=False,
        action="store_true",
        help="If flagged, will remove the output directory before creating it, if it already exists",
    )
    cuts_parser.add_argument(
        "--hide-subtasks",
        action="store_true",
        help="Enable to hide the subtask progress on cuts. This might be if you get annoyed by how buggy it is.",
    )

    # needs: signal, bkgd, bkgdUncertainty, insignificanceThreshold, tree, eventWeight
    optimize_parser = subparsers.add_parser(
        "optimize",
        parents=[main_parser],
        description="Process ROOT ntuples and Optimize Cuts. v.{0}".format(__version__),
        usage="%(prog)s  --signal='Sig*' [..] --bkgd='Bkg*' [...] [options]",
        help="Calculate significances for a series of computed cuts",
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
        epilog="optimize will take in numerous signal, background and calculate the significances for each signal and combine backgrounds automatically.",
    )
    optimize_parser.add_argument(
        "--signal",
        required=True,
        type=str,
        nargs="+",
        metavar="pattern",
        help="signal file patterns",
    )
    optimize_parser.add_argument(
        "--bkgd",
        required=True,
        type=str,
        nargs="+",
        metavar="pattern",
        help="background file patterns",
    )
    optimize_parser.add_argument(
        "--searchDirectory",
        required=False,
        type=str,
        dest="search_directory",
        help="Directory that contains all the cuts.",
        default="cuts",
    )
    optimize_parser.add_argument(
        "--bkgdUncertainty",
        type=float,
        required=False,
        dest="bkgdUncertainty",
        metavar="<sigma>",
        help="background uncertainty for calculating significance",
        default=0.3,
    )
    optimize_parser.add_argument(
        "--bkgdStatUncertainty",
        type=float,
        required=False,
        dest="bkgdStatUncertainty",
        metavar="<sigma>",
        help="background statistical uncertainty for calculating significance",
        default=0.3,
    )
    optimize_parser.add_argument(
        "--insignificance",
        type=float,
        required=False,
        dest="insignificanceThreshold",
        metavar="<min events>",
        help="minimum number of signal events for calculating significance",
        default=0.5,
    )
    optimize_parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        dest="output_directory",
        metavar="<directory>",
        help="output directory to store the <hash>.json files",
        default="significances",
    )
    optimize_parser.add_argument(
        "-n",
        "--max-num-hashes",
        required=False,
        type=int,
        metavar="<n>",
        help="Maximum number of hashes to print for each significance file",
        default=25,
    )

    # needs: supercuts
    hash_parser = subparsers.add_parser(
        "hash",
        parents=[main_parser, supercuts_parser],
        description="Given a hash from optimization, dump the cuts associated with it. v.{0}".format(
            __version__
        ),
        usage="%(prog)s <hash> [<hash> ...] [options]",
        help="Translate hash to cut",
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
        epilog="hash will take in a list of hashes and dump the cuts associated with them",
    )
    hash_parser.add_argument(
        "hash_values",
        type=str,
        nargs="+",
        metavar="<hash>",
        help="Specify a hash to look up the cut for. If --use-summary is flagged, you can pass in a summary.json file instead.",
    )
    hash_parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        dest="output_directory",
        metavar="<directory>",
        help="output directory to store the <hash>.json files",
        default="outputHash",
    )
    hash_parser.add_argument(
        "--use-summary",
        action="store_true",
        help="If flagged, read in the list of hashes from the provided summary.json file",
    )

    summary_parser = subparsers.add_parser(
        "summary",
        parents=[main_parser, parallel_parser],
        description="Given the results of optimize (significances), generate a table of results for each mass point. v.{0}".format(
            __version__
        ),
        usage="%(prog)s [options]",
        help="Summarize Optimization Results",
        formatter_class=lambda prog: CustomFormatter(prog, max_help_position=50),
        epilog="summary will take in significances and summarize in a json file",
    )
    summary_parser.add_argument(
        "--searchDirectory",
        required=False,
        type=str,
        dest="search_directory",
        help="Directory that contains the significances",
        default="significances",
    )
    summary_parser.add_argument(
        "-f",
        "--fmtstr",
        type=str,
        help="format of object names",
        default="([a-zA-Z]+)_(\d+)_(\d+)_(\d+)",
    )
    summary_parser.add_argument(
        "-p",
        "--interpretation",
        type=str,
        help="interpretation of object name",
        default="signal_type:gluino:stop:neutralino",
    )
    summary_parser.add_argument(
        "--output",
        required=False,
        type=str,
        dest="output",
        help="Output json to make",
        default="summary.json",
    )

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
            logger.setLevel(25 - args.verbose * 5)
        else:
            logger.setLevel(logging.NOTSET + 1)

        # call the function and do stuff
        args.func(args)

    except Exception:
        logger.exception("{0}\nAn exception was caught!".format("-" * 20))


if __name__ == "__main__":
    rooptimize()
