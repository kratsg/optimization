import csv
import pdb
with open("signal_scales.txt") as f:
    reader = csv.reader(f, delimiter="\t")
    d = list(reader)
f.close()

cutflows={}
with open("nevents.list") as f:
    reader = csv.reader(f, delimiter=":")
    c = list(reader)
f.close()

for cc in c:
    cutflows[cc[0]] = cc[1]

f = open("signal_weights_new.txt",'w+')
for l in d:
  did = l[1]
  cs = l[3]
  k = l[4]
  filt = l[5]
  try:
    num = cutflows[did] 
  except:
    num = '0'
  f.write('\"' + did + '\":\n')
  f.write('  cross section: ' + cs +'\n')
  f.write('  filter efficiency: ' + filt+'\n')
  f.write('  k-factor: ' + k+'\n')
  f.write('  num events: ' + num+'\n')
f.close()
