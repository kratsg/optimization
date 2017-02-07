#!/usr/bin/env python
# -*- coding: utf-8 -*-,
from __future__ import absolute_import
from __future__ import print_function

__version__ = '0.4.6'
__all__ = ['json_encoder',
           'utils']

import os, sys
# grab the stdout and have python write to this instead
# ROOT will write to the original stdout
STDOUT = os.fdopen(os.dup(sys.stdout.fileno()), 'w')

import logging
logger = logging.getLogger("root_optimize")
logger.addHandler(logging.StreamHandler(STDOUT))
