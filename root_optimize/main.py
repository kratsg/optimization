from __future__ import absolute_import
from __future__ import print_function

import logging
logger = logging.getLogger("root_optimize.main")

from . import utils
import json
import os

def get_summary(filename, mass_windows, stop_masses=[]):
  ''' Primarily used from within do_summary
        - given a significance file, the mass windows, produce a summary dictionary for it
  '''
  logger.info("\treading {0:s}".format(filename))
  with open(filename) as f:
    entry = json.load(f)[0]

    cut_hash     = entry['hash']
    significance = entry['significance_scaled']
    signal_yield = entry['yield_scaled']['sig']
    bkgd_yield   = entry['yield_scaled']['bkg']

    ratio = -1
    try: ratio = signal_yield/bkgd_yield
    except: pass

    did = utils.get_did(os.path.basename(filename))

    m_gluino, m_stop, m_lsp = [int(item) for item in mass_windows.get(did, (0, 0, 0))]
    if not m_stop in stop_masses: return {}

    return {'hash': cut_hash,
            'significance': significance,
            'signal': signal_yield,
            'bkgd': bkgd_yield,
            'ratio': ratio,
            'did': did,
            'm_gluino': int(m_gluino),
            'm_stop': int(m_stop),
            'm_lsp': int(m_lsp)}
