<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Optimization - A PyRoot Codebase](#optimization---a-pyroot-codebase)
  - [Dependencies](#dependencies)
  - [Installing](#installing)
    - [Using a virtual environment to manage python packages](#using-a-virtual-environment-to-manage-python-packages)
    - [... the code](#-the-code)
  - [How to use](#how-to-use)
    - [Grab some optimization ntuples](#grab-some-optimization-ntuples)
    - [Running](#running)
  - [Profiling Code](#profiling-code)
  - [Authors](#authors)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Optimization - A PyRoot Codebase

## Dependencies
 - [PyROOT](https://root.cern.ch/drupal/content/pyroot)
 - [numPy](http://www.numpy.org/)
 - [matplotlib](http://matplotlib.org/)
 - [root\_numpy](http://rootpy.github.io/root_numpy/)

## Installing

### Using a virtual environment to manage python packages

I use [`virtualenvwrapper`](https://virtualenvwrapper.readthedocs.org/en/latest/) to manage my python dependencies and workspace. I assume you have `pip`.

```
pip install virtualenvwrapper
```

and then add the following in your `.bash_profile`

```
source /usr/local/bin/virtualenvwrapper.sh
```

then start a new environment with

```
mkvirtualenv ROOT
```

from now on, everytime I want to use the packages I installed with `pip`, I just type `workon ROOT` to do the trick. Read the [virtualenvwrapper docs](https://virtualenvwrapper.readthedocs.org/en/latest/) for more information.

### ... the code

```
git clone git@github.com:kratsg/Optimization
cd Optimization
workon ROOT
pip install -r requirements.txt
```

Note that I use a virtual environment to put all of my python packages for the Optimization code inside.

## How to use

### Grab some optimization ntuples

I grab a set of optimization ntuples from [faxbox:TheAccountant/Optimizations](http://faxbox.usatlas.org/user/kratsg/TheAccountant/Optimizations) using `xrdcp`

```
xrdcp root://faxbox.usatlas.org//user/kratsg/TheAccountant/Optimization/20150602_1.tar.gz 20150602_1.tar.gz
tar -xzvf 20150602_1.tar.gz
```

### Running

After that, we just (at a bare minimum) specify the `signal` and `bkgd` ROOT files. Since the script takes advantage of `TChain` and \*nix file handling, it will automatically handle multiple files specified for each either as a pattern or just explicitly writing them out.

```
python optimize.py optimize --signal 20150602_1/data-optimizationTree/mc14_13TeV.204533* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --cuts=supercuts.json -b
```

and if you care more about speed, you most likely want to run in batch mode, hence the `-b` option tacked on at the end.

## Profiling Code

This is one of those pieces of python code we always want to run as fast as possible. Optimization should not take long. To figure out those dead-ends, I use [snakeviz](https://jiffyclub.github.io/snakeviz/). The `requirements.txt` file contains this dependency. To run it, I first profile the code by running it:

```bash
python -m cProfile -o profiler.log optimize.py optimize --signal 20150602_1/data-optimizationTree/mc14_13TeV.204533* --bkgd 20150602_1/data-optimizationTree/mc14_13TeV.110* --cuts=supercuts.json -b
```

then I use the `snakeviz` script to help me visualize this

```bash
snakeviz profiler.log
```

and I'm good to go.

## Authors
- [Giordon Stark](https://github.com/kratsg)
