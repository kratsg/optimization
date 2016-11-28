# Optimization - A PyRoot Codebase

This tool allows you to take a series of ROOT ntuples, signal & background, apply a lot of cuts automatically, and figure out the most optimal selections to maximize significance. It comes packed with a lot of features

- generator script to create, what we call, a supercuts file containing all the rules to tell the script what cuts to apply and on which branches
- cut script which will take your signal, background, and supercuts; run them all; and output a series of files with the appropriate event counts for all cuts provided
- optimization script which will take your signal counts and background counts; run them all; and output a sorted list of optimal cuts
- hash look up script to reverse-engineer the cut for a given hash when you supply the supercuts file

*Note*: as part of making the script run as fast as possible, I try to maintain a low memory profile. It will not store (or remember) the cut used to create a significance value. Instead, we compute a 32-bit hash which is used to encode the cuts, and a way to "decode" the hash is also provided.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Major Dependencies](#major-dependencies)
- [Quick Start](#quick-start)
  - [Installing](#installing)
    - [Using virtual environment](#using-virtual-environment)
    - [Without using virtual environment](#without-using-virtual-environment)
    - [Errors with root-numpy and TMVA](#errors-with-root-numpy-and-tmva)
  - [Using](#using)
    - [Grab some optimization ntuples](#grab-some-optimization-ntuples)
    - [Generate a supercuts template](#generate-a-supercuts-template)
    - [Running the cuts](#running-the-cuts)
    - [Calculating the significances](#calculating-the-significances)
    - [Looking up a cut (or two)](#looking-up-a-cut-or-two)
  - [Profiling Code](#profiling-code)
  - [Example Script](#example-script)
- [Documentation](#documentation)
  - [Top-Level](#top-level)
    - [Parameters](#parameters)
  - [Action:Generate](#actiongenerate)
    - [Required Parameters](#required-parameters)
    - [Optional Parameters](#optional-parameters)
    - [Output](#output)
  - [Action:Cut](#actioncut)
    - [Required Parameters](#required-parameters-1)
    - [Optional Parameters](#optional-parameters-1)
    - [Output](#output-1)
  - [Action:Optimize](#actionoptimize)
    - [Required Parameters](#required-parameters-2)
    - [Optional Parameters](#optional-parameters-2)
    - [Output](#output-2)
  - [Action:Hash](#actionhash)
    - [Required Parameters](#required-parameters-3)
    - [Optional Parameters](#optional-parameters-3)
    - [Output](#output-3)
  - [Action:Summary](#actionsummary)
    - [Required Parameters](#required-parameters-4)
    - [Optional Parameters](#optional-parameters-4)
    - [Output](#output-4)
  - [Supercuts File](#supercuts-file)
    - [Defining a fixed cut](#defining-a-fixed-cut)
    - [Defining a supercut](#defining-a-supercut)
    - [Example of a supercuts file](#example-of-a-supercuts-file)
    - [More Complicated Selections](#more-complicated-selections)
- [Authors](#authors)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Major Dependencies
 - [PyROOT](https://root.cern.ch/drupal/content/pyroot) (which technically requires ROOT)
 - [numpy](http://www.numpy.org/)
 - [root\_numpy](http://rootpy.github.io/root_numpy/)

All other dependencies are listed in [requirements.txt](requirements.txt) and can be installed in one line with `pip install -r requirements.txt`.

## Quick Start

tl;dr - copy and paste, and off you go.

### Installing

#### Using virtual environment

I use [`virtualenvwrapper`](https://virtualenvwrapper.readthedocs.org/en/latest/) to manage my python dependencies and workspace. I assume you have `pip`.

```bash
pip install virtualenvwrapper
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile
source ~/.bash_profile
mkvirtualenv optimization
workon optimization
git clone git@github.com:kratsg/Optimization
cd Optimization
pip install numpy
pip install -r requirements.txt
python optimize.py -h
```

Start a new environment with `mkvirtualenv NameOfEnv` and everytime you open a new shell, you just need to type `workon NameOfEnv`. Type `workon` alone to see a list of environments you've created already. Read the [virtualenvwrapper docs](https://virtualenvwrapper.readthedocs.org/en/latest/) for more information.

#### Without using virtual environment

```bash
git clone git@github.com:kratsg/Optimization
cd Optimization
pip install numpy
pip install -r requirements.txt
python optimize.py -h
```

#### Errors with root-numpy and TMVA

ROOT changed the TMVA version so to make `root-numpy` behave nicely, just run

```bash
NOTMVA=1 pip install root-numpy
```

which will install it without TMVA support. Then comment out the relevant line. `root-numpy` also requires `numpy` so you'll want to have that installed beforehand as well.

### Using

#### Grab some optimization ntuples

I grab a set of optimization ntuples from [dropbox](https://www.dropbox.com/sh/s2f5n1oaojnxonn/AABnajIwGGGqMz2RlVO2zjkka?dl=0) and extract them

```bash
tar -xzvf TA07_MBJ10V1.tar.gz
```

#### Generate a supercuts template

A straightforward example is simply just

```bash
python optimize.py generate "Gtt_0L_a/fetch/data-optimizationTree/user.lgagnon:user.lgagnon.370101.Gtt.DAOD_SUSY10.e4049_s2608_r6765_r6282_p2411_tag_10_v1_output_xAOD.root-0.root"
```

which will create a `supercuts.json` file for you to edit so that you can run the optimizations. As a more advanced example, I only wanted to generate a file using a subset of the branches in my file as well as setting some of them to be a fixed cut that I would configure, so I ran

```bash
python optimize.py generate "Gtt_0L_a/fetch/data-optimizationTree/user.lgagnon:user.lgagnon.370101.Gtt.DAOD_SUSY10.e4049_s2608_r6765_r6282_p2411_tag_10_v1_output_xAOD.root-0.root" --fixedBranches multiplicity_topTag* -o dump.json -b -vv --skipBranches *_jet_rc*
```

which will write branches that match `multiplicity_topTag*` to have a fixed cut when I eventually run `optimize` over it; and will also skip branches that match `*_jet_rc*` so they won't be considered at all for cuts.

#### Running the cuts

After that, we just specify all of our ROOT files. The script takes advantage of `TChain` and \*nix file handling, it will automatically handle multiple files specified either as a pattern or just explicitly writing them out. We will group every output by the DID passed in, so please try not to deviate from the default sample names or this breaks the code quite badly.

```bash
python optimize.py cut TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_0L_a -b
python optimize.py cut TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_0L_b -b
python optimize.py cut TA07_MBJ10V1/*_1L/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_1L -b
```

By default, we use `TTree::Draw` in order to calculate the number of events passing a given cut. We will also attempt to parallelize the computations as much as possible. In cases where you have a fast computer and the ntuples are reasonably small (can fit in memory), you might benefit from using a `numpy` boost by adding the `--numpy` flag like so

```bash
python optimize.py cut TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_0L_a -b --numpy
python optimize.py cut TA07_MBJ10V1/*_0L_a/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_0L_b -b --numpy
python optimize.py cut TA07_MBJ10V1/*_1L/fetch/data-optimizationTree/*.root --supercuts=supercuts_small.json -o cuts_1L -b --numpy
```

#### Calculating the significances

After that, we just (at a bare minimum) specify the `signal` and `bkgd` json cut files. The following example takes the `0L_a` files and calculates significances for two different values of luminosity

```bash
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=cuts_0L_a -b --o=significances_0L_a_lumi1 --lumi=1
python optimize.py optimize --signal 37* --bkgd 4* --searchDirectory=cuts_0L_a -b --o=significances_0L_a_lumi2 --lumi=2
```

and this will automatically combine background and produce a significances file for each signal DID passed in.

#### Looking up a cut (or two)

When the optimizations have finished running, you'll want to take the given hash(es) and figure out what cut it corresponds to, you can do this with

```bash
python optimize.py hash e31dcf5ba4786d9e8ffa9e642729a6b9 4e16fdc03c171913bc309d57739c7225 8fa0e0ab6bf6a957d545df68dba97a53 --supercuts=supercuts_small.json
```

which will create `outputHash/<hash>.json` files detailing the cuts involved.

### Profiling Code

This is one of those pieces of python code we always want to run as fast as possible. Optimization should not take long. To figure out those dead-ends, I use [snakeviz](https://jiffyclub.github.io/snakeviz/). The `requirements.txt` file contains this dependency. To run it, I first profile the code by running it:

```bash
python -m cProfile -o profiler.log python optimize.py cut TA06_MBJ05/*_0L/fetch/data-optimizationTree/*.root --supercuts=supercuts.json -o cuts_0L -b --numpy
```

then I use the `snakeviz` script to help me visualize this

```bash
snakeviz profiler.log
```

and I'm good to go.

### Example Script

See [example_script.sh](example_script.sh) for an idea how how to run everything in order to produce a plot of significances.

## Documentation

### Top-Level

```bash
python optimize.py
```

or

```bash
python optimize.py -h
```

```
usage: optimize.py [-h] [-a] {generate,cut,optimize,hash} ...

Author: Giordon Stark. v.eea1e27

positional arguments:
  {generate,cut,optimize,hash}
                              actions available
    generate                  Write supercuts template
    cut                       Apply the cuts
    optimize                  Calculate significances for a series of computed
                              cuts
    hash                      Translate hash to cut

optional arguments:
  -h, --help                  show this help message and exit
  -a, --allhelp               show this help message and all subcommand help
                              messages and exit

This is the top-level. You have no power here.
```

#### Parameters

There is only one required position argument: the `action`. You can choose from

- [generate](#actiongenerate)
- [cut](#actioncut)
- [optimize](#actionoptimize)
- [hash](#actionhash)

We also provide an optional argument `-a, --allhelp` which will print all the help documentation at once instead of just the top-level `-h, --help`.

### Action:Generate

Generate helps you quickly start. Given the ROOT ntuples, generate a supercuts.json template.

```bash
usage: optimize.py generate --signal=signal.root [..] --bkgd=bkgd.root [...] [options]
```

#### Required Parameters

Variable | Type | Description
---------|------|------------
file | string | path to a root file containing an optimization ntuple to use

#### Optional Parameters

Variable | Type | Description
---------|------|------------
-h, --help | bool | display help message | False
-v, --verbose | count | enable more verbose output | 0
--debug | bool | enable full-on debugging | False
-b, --batch | bool | enable batch mode for ROOT | False
--tree | string | ttree name in the ntuples | oTree
--eventWeight | string | event weight branch name | event_weight
--o, --output | string | output json file to store generated supercuts file | supercuts.json
--fixedBranches | strings | branches that should have a fixed cut | []
--skipBranches | strings | branches that should not have a cut (skip them) | []

- `--globalMinVal` is just an aesthetic feature to make it easier to identify the "true" minimum of your ntuples. I often output -99.0 in case there is (for example) no 4th jet, or I could not calculate some substructure information, this allows me to automatically chop off the low end of a branch to get a better calculation of the percentiles
- `--fixedBranches` and `--skipBranches` can take a series of strings or a series of patterns

  ```bash
  --fixedBranches multiplicity_jet multiplicity_topTag_loose multiplicity_topTag_tight
  ```

  or

  ```bash
  --fixedBranches multiplicity_* pt_jet_rc8_1
  ```

  which aims to make life easier for all of us.

#### Output

This script will generate a supercuts json file. See [Supercuts File](#supercuts-file) for more information.

### Action:Cut

Cut helps you by generating the cuts from a supercuts file and applying them to create an output file of counts. Process ROOT ntuples and apply cuts.

```bash
usage: optimize.py cut <file.root> ... [options]
```

#### Required Parameters

Variable | Type | Description
---------|------|------------
files    | string | path(s) to root files containing ntuples

#### Optional Parameters

Variable | Type | Description | Default
---------|------|-------------|---------
-h, --help | bool | display help message | False
-v, --verbose | count | enable more verbose output | 0
--debug | bool | enable full-on debugging | False
-b, --batch | bool | enable batch mode for ROOT | False
--tree | string | ttree name in the ntuples | oTree
--eventWeight | string | event weight branch name | event_weight
--supercuts | string | path to json dict of supercuts for generating cuts | supercuts.json
--weightsFile | string | .json file containing weights in proper formatting - see SampleWeights
--o, --output | directory | output directory to store json files containing cuts | cuts
--numpy | bool | if enabled, use `numpy` and `numexpr` instead of ROOT. [See this section for more information.](#more-complicated-selections)

#### Output

Variable | Type | Description
---------|------|------------
hash | 32-bit string | md5 hash of the cut
raw | integer | raw number of events passing cut
weighted | float | apply event weights to events passing cut
scaled | float | apply sample weights and event weights to events passing cut

Note that weights are applied in order of prominance and specificity: weighted events are applying the monte-carlo event weights (from the generators themselves). Scaled events are with the mc weights applied but also scaled using the sample weights (the ones that differ from sample to sample) and this does not include luminosity at this stage. The calculation of significance includes the luminosity scale factor.

The output is a directory of json files which will look like

```json
{
    ...
    "09a130622e1e6345b83739b3527eccb1": {
        "raw": 90909,
        "scaled": 90909.0,
        "weighted": 2.503
    },
    ...
}
```

This code will group your input files by DIDs and will try its best to do its job to group your sample files.

### Action:Optimize

Optimize helps you find your optimal cuts. Process cuts and determine significance.

```bash
usage: optimize.py optimize  --signal=signal.root [..] --bkgd=bkgd.root [...] [options]
```

**Note**: You can specify multiple backgrounds and multiple signals. Each signal will be run over separately and each background will be merged and treated as a single background.

#### Required Parameters

Variable | Type | Description
---------|------|------------
--signal | string | path(s) to json files containing signal cuts
--bkgd | string | path(s) to json files containing background cuts

**Note**: this will search for files under the `search_directory` option, default is `cuts` to search for files produced by `optimize.py cut`.

#### Optional Parameters

Variable | Type | Description | Default
---------|------|-------------|---------
-h, --help | bool | display help message | False
-v, --verbose | count | enable more verbose output | 0
--debug | bool | enable full-on debugging | False
-b, --batch | bool | enable batch mode for ROOT | False
--searchDirectory | string | the directory that contains all cut.json files | 'cuts'
--bkgdUncertainty | float | bkgd sigma for calculating sig. | 0.3
--bkgdStatUncertainty | float | bkgd statistical uncertainty for significance | 0.3
--insignificance | int | min. number of events for non-zero sig. | 0.5
--o, --output | string | output directory to store significances calculated | significances
--lumi | float | apply the luminosity when calculating significances, to avoid having to redo all the cuts | 1.0
-n, --max-num-hashes | int | maximum number of hashes to dump in the significance files | 25

#### Output

Variable | Type | Description
---------|------|------------
hash | 32-bit string | md5 hash of the cut
significance | float | calculated significance of the cut
yield | float | number of events passing the cut

The output is a directory of json files which will look like

```json
[
    ...
    {
        "hash": "7595976a84303a003f6a4a7458f12b8d",
        "significance_raw": 7.643122000999725,
        "significance_scaled": 4.382066929290212,
        "significance_weighted": 18.34212454602254,
        "yield_raw": { ... },
        "yield_scaled": { ... },
        "yield_weighted": { ... }
    },
    ...
]
```

if a significance was calculated successfully or

```json
[
    ...
    {
        "hash": "c911af35708dcdc51380ebbde81c9b1e",
        "significance_raw": -3,
        "significance_scaled": -1,
        "significance_weighted": -3,
        "yield_raw": { ... },
        "yield_scaled": { ... },
        "yield_weighted": { ... }
    },
    {
        "hash": "b383cea24037667ffb6136d670a33468",
        "significance_raw": -2,
        "significance_scaled": -1,
        "significance_weighted": -2,
        "yield_raw": { ... },
        "yield_scaled": { ... },
        "yield_weighted": { ... }
    },
    {
        "hash": "095414bacf1022f2c941cc6164b175a1",
        "significance_raw": 9.421795580339449,
        "significance_scaled": -2,
        "significance_weighted": 20.37611073465684,
        "yield_raw": { ... },
        "yield_scaled": { ... },
        "yield_weighted": { ... }
    },
    ...
]
```

if the number of events in signal or background did not pass the `--insignificance` minimum threshold set. The significance will always be flagged as a negative number depending on the insignificance observed. The table below summarizes these cases:

Sig. Value | What Happened
----------:|:-------------
-1         | The signal was insignificant
-2         | The background was insignificant
-3         | There were not enough statistics in the background events

Note that `--max-num-hashes` determines how many hashes you will actually see in these output files.

### Action:Hash

Hash to cut translation. Given a hash from optimization, dump the cuts associated with it.

```bash
usage: optimize.py hash <hash> [<hash> ...] [options]
```

#### Required Parameters

Variable | Type | Description
---------|------|------------
hash (positional) | string | 32-bit hash(es) to decode as cuts. If --use-summary is flagged, you can pass in your summary.json file instead.

#### Optional Parameters

Variable | Type | Description| Default
---------|------|------------|---------
-h, --help | bool | display help message | False
-v, --verbose | count | enable more verbose output | 0
--debug | bool | enable full-on debugging | False
-b, --batch | bool | enable batch mode for ROOT | False
--supercuts | string | path to json dict of supercuts | supercuts.json
--o, --output | directory | output directory to store json files containing cuts | outputHash
--use-summary | bool | if enabled, you can pass in your summary.json file instead of a bunch of hashes | False

#### Output

The hash subcommand will create an output directory with multiple json files, one for each hash, containing details about the cut applied. Unlike a standard supercuts file, the hash will only output dictionaries of **4** elements

Variable | Type | Description
---------|------|------------
branch | string | name of branch that cut was applied on
fixed | bool | whether the cut was from a fixed cut or a supercut
pivot | number | the value which we cut on, see `signal_direction` for more
signal_direction | string | `? = >` or `? = <`, cuts obey the rule `value ? pivot`

### Action:Summary

Optimize results to summary json. Given the finished results of an optimization, produce a json summarizing it entirely.

```bash
usage: optimize.py summary --searchDirectory significances/ --massWindows massWindows.txt [options]
```

#### Required Parameters

Variable | Type | Description
---------|------|------------
--searchDirectory | str | The directory containing the significances produced from `optimize.py optimize`
--massWindows | str | The file containing the mapping between DID and mass

#### Optional Parameters

Variable | Type | Description| Default
---------|------|------------|---------
-h, --help | bool | display help message | False
-v, --verbose | count | enable more verbose output | 0
--debug | bool | enable full-on debugging | False
-b, --batch | bool | enable batch mode for ROOT | False
--ncores | int | Number of cores to use for parallelization | <num cores>
-o, --output | str | Name of output file to use | summary.json
--stop-masses | int | Allowed stop masses to include in summary | [5000]

#### Output

The summary subcommand will create an output json file containing a list of dictionaries, one for each signal DID used in optimization. It will contain the following variables in each dictionary:

Variable | Type | Description
---------|------|------------
bkgd | float | Background yield
did | str | DID of signal
hash | 32-bit string | md5 hash of the optimal cut
m_gluino | int | Mass of Gluino
m_lsp | int | Mass of LSP
m_stop | int | Mass of Stop
ratio | float | Ratio of signal/bkgd
significance | float | Significance of optimal cut

This will look something like:

```
[
    ...
    {
        "bkgd": 5.656293846714225,
        "did": "370102",
        "hash": "dc41780c77207a9a5dcf6b97b0cac5ac",
        "m_gluino": 900,
        "m_lsp": 400,
        "m_stop": 5000,
        "ratio": 79.33950854202577,
        "signal": 448.76757396759103,
        "significance": 29.78897424015455
    },
    ...
]
```

### Supercuts File

This is a potentially large [JSON](http://www.json.org/) file that tells the [optimize](#actionoptimize), [hash](#actionhash), and [generate](#actiongenerate) commands the rules of your cuts.

- The `optimize` command uses it to generate a series of cuts to apply to your ntuples, then hash these cuts and store them with their calculated significance.
- The `hash` command uses it to recompute the hash and find the cuts that match up to the hashes you need to decode.
- The `generate` command creates this file for you based on your ntuples to help you get started.

The file will always contain a list of objects (dictionaries) for each branch that you care about cutting on.

#### Defining a fixed cut

A fixed cut is a single cut on a single branch. This is like taking a partial derivative where you fix one thing and vary others. In this case, we fix a branch defined by a fixed cut.

Key | Type | Description
----|------|------------
selections | string | the various selections to apply for the cut
pivot | number | the value at which we cut (or *pivot* against)

The simplest example is when we want to use a single fixed cut on a single branch. Your object will look like

```json
[
    ...
    {
        "selections": "multiplicity_jet > {0}",
        "pivot": 3,
    },
    ...
]
```

This says we would like a fixed cut on `multiplicity_jet` requiring that there are more than 3 jets (eg: the rule we obey is `value > 3`).

#### Defining a supercut

A supercut is our term for an object that generates more than 1 cut on the defined branch. A fixed cut will generate 1 cut, but a supercut can generate a boundless number of cuts.

Key | Type | Description
----|------|------------
selections | string | the various selections to apply for the cut
st3 | list | a list of [start, stop, step] values for each set of pivots

**Note**: the direction in which cuts are generated can be controlled by running cuts in increasing values (`start < stop`, `step > 0`) or decreasing values (`start > stop`, `step < 0`).

There are two main examples we will provide to show the different cuts that could be generated.

```json
[
    ...
    {
        "selections": "multiplicity_jet < {0}",
        "st3": [
            [2, 7, 2]
        ]
    },
    ...
]
```

This says we would like a supercut on `multiplicity_jet` where the pivot values are `2, 4, 6` obeying the rule that `value < pivot`. This supercut will generate 3 cuts:

- `value < 2`
- `value < 4`
- `value < 6`

in that order.

```json
[
    ...
    {
        "selections": "multiplicity_jet > {0}",
        "st3": [
            [3, 1, -1]
        ]
    },
    ...
]
```

This says we would like a supercut on `multiplicity_jet` where the pivot values are `3, 2` obeying the rule that `value > pivot`. This supercut will generate 2 cuts:

- `value > 3`
- `value > 2`

in that order.

#### Example of a supercuts file

Here is an example `supercuts.json` file

```json
[
    {
        "selections": "multiplicity_jet > {0}",
        "st3": [
            [2, 15, 1]
        ]
    },
    {
        "selections": "multiplicity_jet_largeR > {0}",
        "st3": [
            [3, 1, -1]
        ]
    },
    {
        "selections": "multiplicity_topTag_loose > {0}",
        "pivot": [1]
    }
]
```

How do we interpret this? This file tells the code that there are 3 branches to apply cuts on: `multiplicity_jet`, `multiplicity_jet_largeR`, and `multiplicity_topTag_loose`. Each object `{...}` represents a branch. In order:

- This is a supercut. **13** cuts will be generated for `multiplicity_jet` starting from `2` to `15` in increments of `1`. This means the cut values (`pivot`) used will be `2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14` (inclusive start, exclusive end - adhere to python standards). The `signal_direction` specifies where we expect the signal to be. `>` means to cut on the **right** so we only want to keep events with `value > pivot`.
- This is a supercut.**2** cuts will be generated for `multiplicity_jet_largeR` starting from `3` to `1` in incremenets of `-1`. This means the cut values (`pivot`) used will be `3, 2` (inclusive start, exclusive end - adhere to python standards). The `signal_direction` specifies where we expect the signal to be. `<` means to cut on the **left** so we only want to keep events with `value < pivot`.
- This is a fixed cut. **1** cut will be used for `multiplicity_topTag_loose` with a `pivot = 1` and `signal_direction = >`. This means we will only select events with `value > 1` always. The `pivot` will be fixed. One could also fix the cut by providing `start`, `stop`, `step` such that it only generates 1 cut, but the script will not identify this as a fixed cut for you when you look up the `cut` using [hash](#actionhash).

This supercuts file will generate **26** total cuts (`13*2*1 = 26`). Each cut will have an associated hash value and an associated significance which will be recorded to an output file when you run [optimize](#actionoptimize).

If you wish to provide a fixed cut (the pivot does not change), you simply need to specify the pivot instead. Taking the example shown above, you might have something like

```json
[
    {
        "selections": "multiplicity_jet >= {0}",
        "pivot": [4]
    },
    {
        "selections": "multiplicity_jet_largeR > {0}",
        "st3": [
            [3, 1, -1]
        ]
    },
    {
        "selections": "multiplicity_topTag_loose > {0}",
        "pivot": [1]
    }
]
```

which tells the code to always apply a cut of `multiplicity_jet >= 4` always.

#### More Complicated Selections

One can certainly provide more complicated selections involving multiple pivots and multiple branches. In fact, this makes our optimization increasingly more flexible and faster than any other code in existence. If you use `--numpy`, we use the [numexpr](https://github.com/pydata/numexpr/) package to provide the parsing of the more complicated selection strings (they have examples of what you can do). If you do not use `--numpy`, we default to use `ROOT` and `TTree::Draw` to make the cuts, which means a standard `TCut` or `TFormula` can be used for your selection. Either way, you still need to specify placeholders for your pivots.

```json
[
    ...
    {
        "selections": "(mass_jets_largeR_1 > {0} & mass_jets_largeR_2 > {0} & mass_jets_largeR_3 > {0}) >= {1}",
        "st3": [
            [50, 2000, 50],
            [0, 4, 1],
        ]
    },
    ...
]
```

is an example of a perhaps more complicated selection that can be done. In this case, we are determining how many of the 3 leading jets pass a mass cut, but also applying a cut on that count. In this case, the `{0}` pivot placeholder refers to the first `st^3` option: `[50, 2000, 50]` which is to vary the first pivot `{0}` from 50 GeV to 2 TeV in 50 GeV steps. The `{1}` pivot placeholder refers to the second `st^3` option: `[0, 4, 1]` which is to vary the second pivot `{1}` from 0 to 4 in steps of 1. This will allow us to iterate over all possible values of pivots (the product of `[50, 2000, 50] X [0, 4, 1]`).

## Authors
- [Giordon Stark](https://github.com/kratsg)
- [Aviv Cukierman](https://github.com/AvivCukierman)
