# Optimization - A PyRoot Codebase

This tool allows you to take a series of ROOT ntuples, signal & background, apply a lot of cuts automatically, and figure out the most optimal selections to maximize significance. It comes packed with a lot of features

- generator script to create, what we call, a supercuts file containing all the rules to tell the script what cuts to apply and on which branches
  ```
  python optimize.py generate -h
  ```

- optimization script which will take your signal, background, & supercuts; run them all; and output a sorted list of optimal cuts\*
  ```
  python optimize.py optimize -h
  ```

- hash look up script to reverse-engineer the cut for a given hash when you supply the supercuts file
  ```
  python optimize.py hash -h
  ```

\**Note*: as part of making the script run as fast as possible, I try to maintain a low memory profile. It will only pull (load) branches from your ttrees that you plan to make cuts on. It will also not store (or remember) the cut used to create a significance value. Instead, we compute a 32-bit hash which is used to encode the cuts, and a way to "decode" the hash is also provided.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Major Dependencies](#major-dependencies)
- [Quick Start](#quick-start)
  - [Installing](#installing)
    - [Using virtual environment](#using-virtual-environment)
    - [Without using virtual environment](#without-using-virtual-environment)
  - [Using](#using)
    - [Grab some optimization ntuples](#grab-some-optimization-ntuples)
    - [Generate a supercuts template](#generate-a-supercuts-template)
    - [Running the optimizations](#running-the-optimizations)
    - [Looking up a cut (or two)](#looking-up-a-cut-or-two)
  - [Profiling Code](#profiling-code)
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
mkvirtualenv ROOT
workon ROOT
git clone git@github.com:kratsg/Optimization
cd Optimization
pip install -r requirements.txt
python optimize.py -h
```

Start a new environment with `mkvirtualenv NameOfEnv` and everytime you open a new shell, you just need to type `workon NameOfEnv`. Type `workon` alone to see a list of environments you've created already. Read the [virtualenvwrapper docs](https://virtualenvwrapper.readthedocs.org/en/latest/) for more information.

#### Without using virtual environment

```bash
git clone git@github.com:kratsg/Optimization
cd Optimization
pip install -r requirements.txt
python optimize.py -h
```

### Using

#### Grab some optimization ntuples

I grab a set of optimization ntuples from [faxbox:TheAccountant/Optimizations](http://faxbox.usatlas.org/user/kratsg/TheAccountant/Optimizations) using `xrdcp`

```bash
xrdcp root://faxbox.usatlas.org//user/kratsg/TheAccountant/Optimization/20150602_1.tar.gz 20150602_1.tar.gz
tar -xzvf 20150602_1.tar.gz
```

#### Generate a supercuts template

A straightforward example is simply just

```bash
python optimize.py generate --signal 20150602_1/data-optimizationTree/mc14_13TeV.20453* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110*
```

which will create a `supercuts.json` file for you to edit so that you can run the optimizations. As a more advanced example, I only wanted to generate a file using a subset of the branches in my file as well as setting some of them to be a fixed cut that I would configure, so I ran

```bash
python optimize.py generate --signal 20150602_1/data-optimizationTree/mc14_13TeV.20453* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --fixedBranches multiplicity_topTag* -o dump.json -b -vv --skipBranches *_jet_rc*
```

which will write branches that match `multiplicity_topTag*` to have a fixed cut when I eventually run `optimize` over it; and will also skip branches that match `*_jet_rc*` so they won't be considered at all for cuts.

#### Running the optimizations

After that, we just (at a bare minimum) specify the `signal` and `bkgd` ROOT files. Since the script takes advantage of `TChain` and \*nix file handling, it will automatically handle multiple files specified for each either as a pattern or just explicitly writing them out.

```bash
python optimize.py optimize --signal 20150602_1/data-optimizationTree/mc14_13TeV.20453* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --supercuts=supercuts.json -b
```

#### Looking up a cut (or two)

When the optimizations have finished running, you'll want to take the given hash(es) and figure out what cut it corresponds to, you can do this with

```bash
python optimize.py hash e31dcf5ba4786d9e8ffa9e642729a6b9 4e16fdc03c171913bc309d57739c7225 8fa0e0ab6bf6a957d545df68dba97a53 --supercuts=supercuts.json
```

which will create `outputHash/<hash>.json` files detailing the cuts involved.

### Profiling Code

This is one of those pieces of python code we always want to run as fast as possible. Optimization should not take long. To figure out those dead-ends, I use [snakeviz](https://jiffyclub.github.io/snakeviz/). The `requirements.txt` file contains this dependency. To run it, I first profile the code by running it:

```bash
python -m cProfile -o profiler.log optimize.py optimize --signal 20150602_1/data-optimizationTree/mc14_13TeV.204533* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --supercuts=supercuts.json -b
```

then I use the `snakeviz` script to help me visualize this

```bash
snakeviz profiler.log
```

and I'm good to go.

## Documentation

### Top-Level

```bash
python optimize.py -h
```

> usage: optimize.py [-h] [-a] {optimize,generate,hash} ...
>
> Author: Giordon Stark. v.319abfc
>
> positional arguments:
>   {optimize,generate,hash}  actions available
>     optimize                Find optimal cuts
>     generate                Write supercuts template
>     hash                    Translate hash to cut
>
> optional arguments:
>   -h, --help                show this help message and exit
>   -a, --allhelp             show this help message and all subcommand help
>                             messages and exit
>
> This is the top-level. You have no power here. If you want to get started, run
> `optimize.py optimize -h`.

#### Parameters

There is only one required position argument: the `action`. You can choose from

- [optimize](#action:optimize)
- [generate](#action:generate)
- [hash](#action:hash)

We also provide an optional argument `-a, --allhelp` which will print all the help documentation at once instead of just the top-level `-h, --help`.

### Action:Optimize

Optimize helps you find your optimal cuts.

```bash
python optimize.py optimize -h
```

#### Required Parameters

Variable | Type | Description
---------|------|------------

#### Optional Parameters

Variable | Type | Description
---------|------|------------

### Action:Generate

Generate helps you quickly start.

```bash
python optimize.py optimize -h
```

#### Required Parameters

Variable | Type | Description
---------|------|------------

#### Optional Parameters

Variable | Type | Description
---------|------|------------


### Action:Hash

Generate helps you decode the hash.

```bash
python optimize.py optimize -h
```

#### Required Parameters

Variable | Type | Description
---------|------|------------

#### Optional Parameters

Variable | Type | Description
---------|------|------------


### Supercuts File

This is a potentially large [JSON](http://www.json.org/) file that tells the [optimize](#action:optimize), [hash](#action:hash), and [generate](#action:generate) commands the rules of your cuts.

- The `optimize` command uses it to generate a series of cuts to apply to your ntuples, then hash these cuts and store them with their calculated significance.
- The `hash` command uses it to recompute the hash and find the cuts that match up to the hashes you need to decode.
- The `generate` command creates this file for you based on your ntuples to help you get started.

The file will always contain a list of objects (dictionaries) for each branch that you care about cutting on.

#### Defining a fixed cut

A fixed cut is a single cut on a single branch. This is like taking a partial derivative where you fix one thing and vary others. In this case, we fix a branch defined by a fixed cut.

Key | Type | Description
----|------|------------
branch | string | name of branch to apply a selection on
pivot | number | the value at which we cut (or *pivot* against)
signal_direction | string | `?= >, <`. Obeys the rule: `value ? pivot`

The simplest example is when we want to use a single fixed cut on a single branch. Your object will look like

```json
[
  ...
  {
    "branch": "multiplicity_jet",
    "pivot": 3,
    "signal_direction": ">"
  },
  ...
]
```

This says we would like a fixed cut on `multiplicity_jet` requiring that there are more than 3 jets (eg: the rule we obey is `value > 3`).

#### Defining a supercut

A supercut is our term for an object that generates more than 1 cut on the defined branch. A fixed cut will generate 1 cut, but a supercut can generate a boundless number of cuts.

Key | Type | Description
----|------|------------
branch | string | name of branch to apply a selection on
start | number | (inclusive) starting value for the `pivot`
stop | number | (exclusive) ending value for the `pivot`
step | number | (non-zero) increment or decrement to take to go from `start` to `stop`
signal_direction | string | `?= >, <`. Obeys the rule: `value ? pivot`

**Note**: the direction in which cuts are generated can be controlled by running cuts in increasing values (`start < stop`, `step > 0`) or decreasing values (`start > stop`, `step < 0`).

There are two main examples we will provide to show the different cuts that could be generated.

```json
[
  ...
  {
    "branch": "multiplicity_jet",
    "start": 2,
    "stop": 7,
    "step": 2,
    "signal_direction": "<"
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
    "branch": "multiplicity_jet",
    "start": 3,
    "stop": 1,
    "step": -1,
    "signal_direction": ">"
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
    "branch": "multiplicity_jet",
    "start": 2,
    "stop": 15,
    "step": 1,
    "signal_direction": ">"
  },
  {
    "branch": "multiplicity_jet_largeR",
    "start": 3,
    "stop": 1,
    "step": -1,
    "signal_direction": "<"
  },
  {
    "branch": "multiplicity_topTag_loose",
    "pivot": 1,
    "signal_direction": ">"
  }
]
```

How do we interpret this? This file tells the code that there are 3 branches to apply cuts on: `multiplicity_jet`, `multiplicity_jet_largeR`, and `multiplicity_topTag_loose`. Each object `{...}` represents a branch. In order:

- This is a supercut. **13** cuts will be generated for `multiplicity_jet` starting from `2` to `15` in increments of `1`. This means the cut values (`pivot`) used will be `2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14` (inclusive start, exclusive end - adhere to python standards). The `signal_direction` specifies where we expect the signal to be. `>` means to cut on the **right** so we only want to keep events with `value > pivot`.
- This is a supercut.**2** cuts will be generated for `multiplicity_jet_largeR` starting from `3` to `1` in incremenets of `-1`. This means the cut values (`pivot`) used will be `3, 2` (inclusive start, exclusive end - adhere to python standards). The `signal_direction` specifies where we expect the signal to be. `<` means to cut on the **left** so we only want to keep events with `value < pivot`.
- This is a fixed cut. **1** cut will be used for `multiplicity_topTag_loose` with a `pivot = 1` and `signal_direction = >`. This means we will only select events with `value > 1` always. The `pivot` will be fixed. One could also fix the cut by providing `start`, `stop`, `step` such that it only generates 1 cut, but the script will not identify this as a fixed cut for you when you look up the `cut` using [hash](#action:hash).

This supercuts file will generate **26** total cuts (`13*2*1 = 26`). Each cut will have an associated hash value and an associated significance which will be recorded to an output file when you run [optimize](#action:optimize)

## Authors
- [Giordon Stark](https://github.com/kratsg)
