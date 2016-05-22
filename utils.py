import csv
import re

import logging
logger = logging.getLogger("optimize")

def load_mass_windows(filename):
  with open(filename, 'r') as f:
    return {l[0]: tuple(l[1:4]) for l in csv.reader(f, delimiter='\t')}

#@echo(write=logger.debug)
did_regex = re.compile('\.?(?:00)?(\d{6,8})\.?')
def get_did(filename):
  global did_regex
  m = did_regex.search(filename.split("/")[-1])
  if m is None:
    logger.warning('Can\'t figure out the DID! Using input filename: {0}'.format(filename))
    return filename.split("/")[-1]
  return m.group(1)

