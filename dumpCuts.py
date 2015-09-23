import json
import glob
import os
for filename in glob.glob("CR1Cuts/*.json"):
  did = os.path.basename(filename).rstrip(".json")
  with open(filename, 'r') as f:
    vals = json.load(f)["080bca720e0e3e27655ccddc6d06a3ec"]
  print "{0:6s}\t{1:10.2f}\t{2:10.2f}\t{3:10.2f}".format(did, vals['raw'], vals['weighted'], vals['scaled'])

