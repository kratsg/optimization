import csv
import re
import json

import logging
logger = logging.getLogger("optimize")
logger.addHandler(logging.NullHandler())

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

#@echo(write=logger.debug)
def read_supercuts_file(filename):
  logger.info("Reading supercuts file {0}".format(filename))
  logger.info("\tOpening")
  with open(filename) as f:
    supercuts = json.load(f)

  logger.info("\tLoaded")
  selections= set([supercut['selections'] for supercut in supercuts])
  try:
    for supercut in supercuts:
      selections.remove(supercut['selections'])
  except KeyError:
    raise KeyError("Found more than one supercut definition on {0}".format(supercut['selections']))

  logger.info("\tFound {1:d} supercut definitions".format(filename, len(supercuts)))
  return supercuts
