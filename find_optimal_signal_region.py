import argparse
import subprocess
import os

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: A. Cukierman, G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('--lumi', required=False, type=int, dest='lumi', metavar='<L>', help='luminosity to use', default=1)
parser.add_argument('-o', '--output', required=False, type=str, dest='output', metavar='', help='basename to use for output filename', default='output')
parser.add_argument('-d', '--output-dir', required=False, type=str, dest='output_dir', metavar='', help='directory to put it in', default='plots')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
import csv
import glob
import re
import json
from collections import defaultdict

def init_canvas():
  c = ROOT.TCanvas("c", "", 0, 0, 800, 600)
  c.SetRightMargin(0.16)
  c.SetTopMargin(0.07)
  return c

def init_hist(label):
  return ROOT.TH2F("grid", ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % label, 12, 800, 2000, 13, 0, 1300)

def draw_hist(h):
  # now draw it
  h.SetMarkerSize(1.5)
  h.SetMarkerColor(ROOT.kWhite)
  ROOT.gStyle.SetPalette(51)
  ROOT.gStyle.SetPaintTextFormat("1.0f")
  h.Draw("TEXT COLZ")

def draw_text(args):
  txt = ROOT.TLatex()
  txt.SetNDC()
  txt.DrawText(0.32,0.87,"Internal")
  txt.DrawText(0.2,0.82,"Simulation")
  txt.SetTextSize(0.030)
  txt.DrawLatex(0.16,0.95,"#tilde{g}-#tilde{g} production, #tilde{g} #rightarrow t #bar{t} + #tilde{#chi}^{0}_{1}")
  txt.DrawLatex(0.62,0.95,"L_{int} = %d fb^{-1}, #sqrt{s} = 13 TeV"% args.lumi)
  txt.SetTextFont(72)
  txt.SetTextSize(0.05)
  txt.DrawText(0.2,0.87,"ATLAS")
  txt.SetTextFont(12)
  txt.SetTextAngle(38)
  txt.SetTextSize(0.02)
  txt.DrawText(0.33,0.63,"Kinematically Forbidden")

def fix_zaxis(h):
  # fix the ZAxis
  h.GetZaxis().SetRangeUser(1, 5)
  h.GetZaxis().CenterLabels()
  h.GetZaxis().SetTickLength(0)
  h.SetContour(4)
  h.GetZaxis().SetNdivisions(4, False)

def draw_line():
  topmass = 173.34
  l=ROOT.TLine(1000,1000,2000,2000)
  l.SetLineStyle(2)
  l.DrawLine(800,800-2*topmass,1300+2*topmass,1300)

def save_canvas(c, filename):
  c.SaveAs(filename + ".pdf")
  print "Saving file " + filename
  c.Clear()

from rootpy.plotting.style import set_style, get_style
set_style('ATLAS')

# given a DID, we get the mass points, translates to a box on the graph for us
with open('mass_windows.txt', 'r') as f:
  reader = csv.reader(f, delimiter='\t')
  m = list(reader)
mdict = {l[0]: [int(l[1]),int(l[2]),int(l[3])] for l in m}
del m

# start up a dictionary to hold all information
significances = defaultdict(lambda: {1: 0, 2: 0, 3: 0, 4: 0})

p_did = re.compile('s(\d+)\.b([0-9\-]+)\.json')

# for each signal region, build up the significance value
for i in range(1,5):
  files = glob.glob("SR{0:d}Significances_{1:d}/s*.b*.json".format(i, args.lumi))
  for filename in files:
    with open(filename, 'r') as f:
      data = json.load(f)
    did = p_did.search(filename).group(1)
    significances[did][i] = data[0]['significance_scaled']

import operator
winners = {1: 0, 2: 0, 3: 0, 4: 0}
for did, vals in significances.iteritems():
  winners[max(vals.iteritems(), key=operator.itemgetter(1))[0]] += 1

print winners

c = init_canvas()
h = init_hist("Optimal Signal Region")
for did, vals in significances.iteritems():
  winningSR = max(vals.iteritems(), key=operator.itemgetter(1))[0]
  mgluino, mstop, mlsp = mdict[did]
  if mstop != 5000: continue

  # now, let's find the bin to fill
  b = h.FindFixBin(mgluino, mlsp)
  xx = yy = zz = ROOT.Long(0)
  h.GetBinXYZ(b, xx, yy, zz)
  if xx != 0 or yy != 0 or zz != 0:
    print "bin was already set?\n\txx: {0}\n\tyy: {1}\n\tzz: {2}".format(xx, yy, zz)
    print "mgluino: {0}\tmlsp: {1}".format(mgluino, mlsp)
    print "new value: {0}".format(winningSR)
    print "-"*20
  h.SetBinContent(b, winningSR)

draw_hist(h)
draw_text(args)
fix_zaxis(h)
draw_line()
save_canvas(c, '{0}_optimalSR_grid_lumi{1}'.format(os.path.join(args.output_dir, args.output), args.lumi))

