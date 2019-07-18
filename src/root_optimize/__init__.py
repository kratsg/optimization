#!/usr/bin/env python
# -*- coding: utf-8 -*-,
from __future__ import absolute_import
from __future__ import print_function

__all__ = ['json_encoder',
           'utils']

from .version import __version__

# Set up ROOT
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(True)

import logging
from .utils import TqdmLoggingHandler
logger = logging.getLogger("root_optimize")
logger.addHandler(TqdmLoggingHandler())
