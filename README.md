# Optimization - A PyRoot Codebase

This tool allows you to take a series of ROOT ntuples, signal & background, apply a lot of cuts automatically, and figure out the most optimal selections to maximize significance. It comes packed with a lot of features

- generator script to create, what we call, a supercuts file containing all the rules to tell the script what cuts to apply and on which branches
- optimization script which will take your signal, background, & supercuts; run them all; and output a sorted list of optimal cuts\*
- hash look up script to reverse-engineer the cut for a given hash when you supply the supercuts file

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
python optimize.py optimize --signal 20150602_1/data-optimizationTree/mc14_13TeV.20453* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --cuts=supercuts.json -b
```

#### Looking up a cut (or two)

When the optimizations have finished running, you'll want to take the given hash(es) and figure out what cut it corresponds to, you can do this with

```bash
python optimize.py hash e31dcf5ba4786d9e8ffa9e642729a6b9 4e16fdc03c171913bc309d57739c7225 8fa0e0ab6bf6a957d545df68dba97a53 --cuts=supercuts.json
```

which will create `outputHash/<hash>.json` files detailing the cuts involved.

### Profiling Code

This is one of those pieces of python code we always want to run as fast as possible. Optimization should not take long. To figure out those dead-ends, I use [snakeviz](https://jiffyclub.github.io/snakeviz/). The `requirements.txt` file contains this dependency. To run it, I first profile the code by running it:

```bash
python -m cProfile -o profiler.log optimize.py optimize --signal 20150602_1/data-optimizationTree/mc14_13TeV.204533* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --cuts=supercuts.json -b
```

then I use the `snakeviz` script to help me visualize this

```bash
snakeviz profiler.log
```

and I'm good to go.

# Authors
- [Giordon Stark](https://github.com/kratsg)
