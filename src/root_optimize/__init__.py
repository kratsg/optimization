#!/usr/bin/env python
# -*- coding: utf-8 -*-,
from __future__ import absolute_import
from __future__ import print_function

__all__ = ["json_encoder", "utils"]

import logging
from .utils import TqdmLoggingHandler

logger = logging.getLogger("root_optimize")
logger.addHandler(TqdmLoggingHandler())
