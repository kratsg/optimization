#!/usr/bin/env python
import io, os, sys

# Check Python version
if sys.version_info < (2, 6):
    sys.exit("root_optimize only supports python 2.6 and above")

# do the setup
from setuptools import setup
from root_optimize import __version__

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read(os.path.join(here, 'README.rst'))

setup(
    name='root_optimize',
    version=__version__,
    description='Perform optimizations on flat ROOT TTrees',
    author='Giordon Stark',
    author_email='kratsg@gmail.com',
    url='https://github.com/kratsg/Optimization',
    packages=['root_optimize'],
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities',
    ],
    install_requires=[
      'Pygments==2.0.2',
      'backports.ssl-match-hostname==3.4.0.2',
      'brewer2mpl==1.4.1',
      'certifi==2015.04.28',
      'joblib==0.8.4',
      'matplotlib==1.4.2',
      'mock==1.0.1',
      'nose==1.3.4',
      'numexpr==2.4.3',
      'pudb==2015.1',
      'pyparsing==2.0.3',
      'python-dateutil==2.4.0',
      'pytz==2014.10',
      'root-numpy>=4.6.0',
      'rootpy>=0.8.0',
      'six==1.9.0',
      'snakeviz==0.4.0',
      'tornado==4.2',
      'urwid==1.3.0',
      'wsgiref==0.1.2'
    ],
    entry_points = {
      'console_scripts': ['rooptimize=root_optimize.command_line:main']
    }
)
