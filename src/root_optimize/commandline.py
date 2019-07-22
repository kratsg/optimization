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
import click
import argparse
import json
import hashlib
import copy
import operator
import glob
import os
from collections import defaultdict
import tempfile
import tqdm
import uproot

# root_optimize
from . import utils
from .json import NoIndent, NoIndentEncoder
from .version import __version__

# parallelization (http://blog.dominodatalab.com/simple-parallelization/)
from joblib import Parallel, delayed
import multiprocessing

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
                                k: (NoIndent(v) if k == "pivot" else v)
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
    if not os.path.exists(args.mass_windows):
        raise IOError(
            "Cannot find the mass_windows file: {0:s}".format(args.mass_windows)
        )

    mass_windows = utils.load_mass_windows(args.mass_windows)
    num_cores = min(multiprocessing.cpu_count(), args.num_cores)
    logger.log(25, "Using {0} cores".format(num_cores))
    results = Parallel(n_jobs=num_cores)(
        delayed(utils.get_summary)(filename, mass_windows, args.stop_masses)
        for filename in glob.glob(os.path.join(args.search_directory, "s*.b*.json"))
    )
    results = filter(None, results)
    logger.log(25, "Generated summary for {0} items".format(len(results)))

    with open(args.output, "w+") as f:
        f.write(
            json.dumps(
                sorted(results, key=operator.itemgetter("did")),
                sort_keys=True,
                indent=4,
            )
        )

    return True


# This is the start of the CLI
# set verbosity for python printing
with utils.stdout_redirect_to_tqdm():
    try:

        @click.group(
            context_settings=dict(help_option_names=['-h', '--help']),
            epilog='Author: Giordon Stark',
        )
        @click.version_option(version=__version__)
        @click.option('-v', '--verbose', count=True)
        def rooptimize(verbose):
            if verbose < 5:
                logger.setLevel(25 - verbose * 5)
            else:
                logger.setLevel(logging.NOTSET + 1)

        @rooptimize.command(short_help='Write supercuts template')
        @click.argument('file')
        @click.option(
            '-t', '--tree-name', default='nominal', help='Tree name to use for file'
        )
        @click.option(
            '-o',
            '--output',
            default=None,
            help='output json file to store the generated supercuts template',
        )
        @click.option(
            '--fixedBranches', multiple=True, help='branches that should remain fixed'
        )
        @click.option(
            '--skipBranches', multiple=True, help='branches that should be skipped'
        )
        def generate(file, tree_name, output, fixedbranches, skipbranches):
            """Given a single FILE that contains the general structure of the tree, generate a supercuts file that works on it."""
            # this is a dict that holds the tree
            tree = uproot.open(file)[tree_name]

            supercuts = []

            for b in tree.keys():
                if utils.match_branch(b, skipbranches):
                    logger.log(25, "{0:32s}:\tSkipping as requested".format(b))
                    continue

                if utils.match_branch(b, fixedbranches):
                    supercuts.append(
                        {"selections": "{0:s} > {{0}}".format(b), "pivot": 0}
                    )
                else:
                    supercuts.append(
                        {
                            "selections": "{0:s} > {{0}}".format(b.decode('utf-8')),
                            "st3": [NoIndent([0.0, 10.0, 1.0])],
                        }
                    )

            result = json.dumps(
                sorted(supercuts, key=operator.itemgetter("selections")),
                sort_keys=True,
                indent=4,
                cls=NoIndentEncoder,
            )

            if output is None:
                click.echo(result)
            else:
                with open(output, "w+") as f:
                    f.write(result)

        @rooptimize.command(
            short_help='Apply the cuts',
            epilog='cut will take in a series of files and calculate the unscaled and scaled counts for all cuts possible.',
        )
        @click.argument('files', nargs=-1, type=click.Path())
        @click.option(
            '--tree-names',
            multiple=True,
            default=['oTree'],
            help="names of the tree containing the ntuples",
        )
        @click.option(
            '--eventWeight',
            default='weight_mc',
            help='event weight in the ntuples. It must exist.',
        )
        @click.option('--supercuts', default='supercuts.json', type=click.Path())
        @click.option(
            '--ncores',
            default=multiprocessing.cpu_count(),
            help='Number of cores to use for parallelization. Defaults to max.',
        )
        @click.option(
            '-o',
            '--output-directory',
            default='cuts',
            help='output directory to store the <hash>.json files',
        )
        @click.option(
            '--weightsFile',
            default='weights.json',
            help='json file containing weights by DSID',
        )
        @click.option(
            '--overwrite/--no-overwrite',
            default=False,
            help="If flagged, will remove the output directory before creating it, if it already exists",
        )
        @click.option(
            '--show-subtasks/--hide-subtasks',
            default=True,
            help="Show or hide the subtask progress on cuts. This might be needed if you get annoyed by how buggy the output looks.",
        )
        def cuts(
            files,
            tree_names,
            eventweight,
            supercuts,
            ncores,
            output_directory,
            weightsfile,
            overwrite,
            show_subtasks,
        ):
            """Process ROOT ntuples and apply cuts"""
            # before doing anything, let's ensure the directory we make is ok
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            elif overwrite:
                import shutil

                shutil.rmtree(output_directory)
            else:
                raise IOError(
                    "Output directory already exists: {0:s}".format(output_directory)
                )

            if len(tree_names) == 1 and len(files) > 1:
                tree_names *= len(files)
            if len(tree_names) != len(files):
                raise ValueError(
                    "You gave us incompatible numbers of files ({}) and tree names ({})".format(
                        len(files), len(tree_names)
                    )
                )

            # first step is to group by the sample DID
            dids = defaultdict(list)
            trees = {}
            for fname, tname in zip(files, tree_names):
                did = utils.get_did(fname)
                dids[did].append(fname)
                if trees.setdefault(did, tname) != tname:
                    raise ValueError(
                        'Found incompatible tree names ({}, {}) for the same DSID ({})'.format(
                            tname, trees[did], did
                        )
                    )

            # load in the supercuts file
            supercuts = utils.read_supercuts_file(supercuts)

            # load up the weights file
            if not os.path.isfile(weightsfile):
                raise ValueError(
                    "The supplied weights file `{0}` does not exist or I cannot find it.".format(
                        weightsfile
                    )
                )
            else:
                weights = json.load(open(weightsfile))

            # parallelize
            num_cores = min(multiprocessing.cpu_count(), ncores)
            logger.log(25, "Using {0} cores".format(num_cores))

            pids = None
            # if pids is None, do_cut() will disable the progress
            if show_subtasks:
                from numpy import memmap, uint64

                pids = memmap(
                    os.path.join(tempfile.mkdtemp(), "pids"),
                    dtype=uint64,
                    shape=num_cores,
                    mode="w+",
                )

            overall_progress = tqdm.tqdm(
                total=len(dids),
                desc="Num. files",
                position=0,
                leave=True,
                unit="file",
                dynamic_ncols=True,
            )

            class CallBack(object):
                completed = defaultdict(int)

                def __init__(self, index, parallel):
                    self.index = index
                    self.parallel = parallel

                def __call__(self, index):
                    CallBack.completed[self.parallel] += 1
                    overall_progress.update()
                    overall_progress.refresh()
                    if self.parallel._original_iterable:
                        self.parallel.dispatch_next()

            import joblib.parallel

            joblib.parallel.CallBack = CallBack

            results = Parallel(n_jobs=num_cores)(
                delayed(utils.do_cut)(
                    did,
                    files,
                    supercuts,
                    weights,
                    trees[did],
                    output_directory,
                    eventweight,
                    pids,
                )
                for did, files in dids.items()
            )

            overall_progress.close()

            for did, result in zip(dids, results):
                logger.log(
                    25, "DID {0:s}: {1:s}".format(did, "ok" if result[0] else "not ok")
                )

            logger.log(
                25,
                "Total CPU elapsed time: {0}".format(
                    utils.secondsToStr(sum(result[1] for result in results))
                ),
            )

            return True

        @rooptimize.command(
            short_help='Calculate significances for a series of computed cuts',
            epilog='optimize will take in numerous signal, background and calculate the significances for each signal and combine backgrounds automatically.',
        )
        @click.option('--signal', multiple=True, help='signal file pattern')
        @click.option('--bkgd', multiple=True, help='background file pattern')
        @click.option('--did-to-group', help='json dict mapping a did to a group')
        @click.option(
            '--searchDirectory',
            default='cuts',
            help='Directory that contains all the json files.',
        )
        @click.option(
            '--bkgdUncertainty',
            default=0.3,
            help='background uncertainty for calculating significance',
        )
        @click.option(
            '--bkgdStatUncertainty',
            default=0.3,
            help='background statistical uncertainty for calculating significance',
        )
        @click.option(
            '--insignificanceThreshold',
            default=0.5,
            help='minimum number of signal events for calculating significance',
        )
        @click.option(
            '--lumi',
            default=1.0,
            help='Apply a global luminosity scale factor (units are ifb)',
        )
        @click.option(
            '--rescale',
            help='json dict of groups and dids to apply a scale factor to. If not provided, no scaling will be done.',
        )
        @click.option(
            '-o',
            '--output',
            default='significances',
            help='output directory to store the <hash>.json files',
        )
        @click.option(
            '-n',
            '--max-num-hashes',
            default=25,
            help='Maximimum number of hashes to print for each significance file',
        )
        def optimize(
            signal,
            bkgd,
            did_to_group,
            searchdirectory,
            bkgduncertainty,
            bkgdstatuncertainty,
            insignificancethreshold,
            lumi,
            rescale,
            output,
            max_num_hashes,
        ):
            """Process ROOT ntuples and Optimize Cuts."""
            # before doing anything, let's ensure the directory we make is ok
            if not os.path.exists(output):
                os.makedirs(output)
            else:
                raise IOError("Output directory already exists: {0:s}".format(output))

            rescale = None
            did_to_group = None
            if rescale:
                rescale = json.load(open(rescale))
                if did_to_group is None:
                    raise ValueError(
                        "If you are going to rescale, you need to pass in the --did-to-group mapping dict."
                    )
                did_to_group = json.load(open(did_to_group))

            logger.log(
                25, "Reading in all background files to calculate total background"
            )

            total_bkgd = defaultdict(
                lambda: {"raw": 0.0, "weighted": 0.0, "scaled": 0.0}
            )
            bkgd_dids = []

            # make sure messages are only logged once, not multiple times
            duplicate_log_filter = utils.DuplicateFilter()
            logger.addFilter(duplicate_log_filter)

            # for each bkgd file, open, read, load, and combine
            for b in bkgd:
                # expand out patterns if needed
                for fname in glob.glob(os.path.join(searchdirectory, b)):
                    did = utils.get_did(fname)
                    logger.log(25, "\tLoading {0:s} ({1:s})".format(did, fname))
                    # generate a list of background dids
                    bkgd_dids.append(did)
                    with open(fname, "r") as f:
                        bkgd_data = json.load(f)
                        for cuthash, counts_dict in bkgd_data.items():
                            for counts_type, counts in counts_dict.items():
                                total_bkgd[cuthash][counts_type] += counts
                                if counts_type == "scaled" and rescale:
                                    if did in rescale:
                                        scale_factor = rescale.get(did, 1.0)
                                        total_bkgd[cuthash][counts_type] *= scale_factor
                                        logger.log(
                                            25,
                                            "\t\tApplying scale factor for DID#{0:s}: {1:0.2f}".format(
                                                did, scale_factor
                                            ),
                                        )
                                    if did_to_group[did] in rescale:
                                        scale_factor = rescale.get(
                                            did_to_group[did], 1.0
                                        )
                                        logger.log(
                                            25,
                                            '\t\tApplying scale factor for DID#{0:s} because it belongs in group "{1:s}": {2:0.2f}'.format(
                                                did, did_to_group[did], scale_factor
                                            ),
                                        )
                                        total_bkgd[cuthash][counts_type] *= scale_factor

            # remove the filter and clear up memory of stored logs
            logger.removeFilter(duplicate_log_filter)
            del duplicate_log_filter

            # create hash for background
            bkgdHash = hashlib.md5(str(sorted(bkgd_dids)).encode('utf-8')).hexdigest()
            logger.log(25, "List of backgrounds produces hash: {0:s}".format(bkgdHash))
            # write the backgrounds to a file
            with open(os.path.join(output, "{0:s}.json".format(bkgdHash)), "w+") as f:
                f.write(json.dumps(sorted(bkgd_dids)))

            logger.log(25, "Calculating significance for each signal file")
            # for each signal file, open, read, load, and divide with the current background
            for sig in signal:
                # expand out patterns if needed
                for fname in glob.glob(os.path.join(searchdirectory, sig)):
                    did = utils.get_did(fname)
                    logger.log(
                        25,
                        "\tCalculating significances for {0:s} ({1:s})".format(
                            did, fname
                        ),
                    )
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
                                            lumi * 1000 * counts,
                                            lumi
                                            * 1000
                                            * total_bkgd[cuthash][counts_type],
                                            insignificancethreshold,
                                            bkgduncertainty,
                                            bkgdstatuncertainty,
                                            total_bkgd[cuthash]["raw"],
                                        ),
                                    )
                                    for counts_type, counts in counts_dict.items()
                                ]
                                + [
                                    (
                                        "yield_{0:s}".format(counts_type),
                                        {
                                            "sig": lumi * 1000 * counts,
                                            "bkg": lumi
                                            * 1000
                                            * total_bkgd[cuthash][counts_type],
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
                            output, "s{0:s}.b{1:s}.json".format(did, bkgdHash)
                        ),
                        "w+",
                    ) as f:
                        f.write(
                            json.dumps(
                                sorted(
                                    significances,
                                    key=operator.itemgetter("significance_scaled"),
                                    reverse=True,
                                )[:max_num_hashes],
                                sort_keys=True,
                                indent=4,
                            )
                        )

            return True

        @rooptimize.command(
            short_help='Translate hash to cut',
            epilog='hash will take in a list of hashes and dump the cuts associated with them',
        )
        @click.argument('hash', nargs=-1)
        @click.option('--supercuts', default='supercuts.json', type=click.Path())
        @click.option(
            '-o',
            '--output',
            default='outputHash',
            help='output directory to store the <hash>.json files',
        )
        @click.option(
            '--use-summary/--no-use-summary',
            default=True,
            help='If flagged, read in the list of hashes from the provided summary.json file',
        )
        def hash():
            """Look up the cut(s) for a HASH from an optimization. If --use-summary is flagged, you can pass in a summary.json file instead."""
            pass

        @rooptimize.command(
            short_help='Summarize Optimization Results',
            epilog='summary will take in significances and summarize in a json file',
        )
        @click.option(
            '--ncores',
            default=multiprocessing.cpu_count(),
            help='Number of cores to use for parallelization. Defaults to max.',
        )
        @click.option(
            '--searchDirectory',
            default='cuts',
            help='Directory that contains the significances.',
        )
        @click.option('--massWindows', help='File that maps DID to mass.')
        @click.option(
            '-o', '--output', default='summary.json', help='Output json to make'
        )
        @click.option(
            '--stop-masses', multiple=True, default=5000, help='Allowed stop masses'
        )
        def summary():
            """Given the results of optimize (significances), generate a table of results for each mass point."""
            pass

        # set the functions that get called with the given arguments
        # cuts_parser.set_defaults(func=do_cuts)
        # optimize_parser.set_defaults(func=do_optimize)
        # generate_parser.set_defaults(func=do_generate)
        # hash_parser.set_defaults(func=do_hash)
        # summary_parser.set_defaults(func=do_summary)

    except Exception:
        logger.exception("{0}\nAn exception was caught!".format("-" * 20))
