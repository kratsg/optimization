*** Running on LXPLUS/afs

These are some instructions that I used to get this working in an ATLAS environment. Hopefully this is useful for someone.

To install:

```
setupATLAS
virtualenv -p `which python` ROOT
source ROOT/bin/activate
localSetupROOT
localSetupSFT --cmtConfig=x86_64-slc6-gcc48-opt pyanalysis/1.4_python2.7
localSetupGcc gcc493_x86_64_slc6
env CXX=`which g++` pip install numexpr
easy_install -U setuptools
pip install -r requirements.txt
```

Then you should be able to run:

```
python optimize.py -h
```

And to set it up in the future, just do:

```
setupATLAS
source ROOT/bin/activate
localSetupROOT
localSetupSFT --cmtConfig=x86_64-slc6-gcc48-opt pyanalysis/1.4_python2.7
python optimize.py -h
```
