import argparse
import subprocess
import os
import utils
import csv
import json

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
  pass

__version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
__short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

parser = argparse.ArgumentParser(description='Author: A. Cukierman, G. Stark. v.{0}'.format(__version__),
                                 formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
parser.add_argument('--summary', type=str, required=True, help='Summary json')
parser.add_argument("--outputHash", type=str, required=True, help="directory where outputHash files are located")
parser.add_argument("--supercuts", type=str, required=True, help="supercuts file detailing all selections used")
parser.add_argument('--lumi', type=float, required=False, help='Luminosity to write on plot [ifb]', default=35)
parser.add_argument('--text-file', type=str, required=False, help='text csv file', default=None)
parser.add_argument('--out-directory', type=str, required=False, help='output directory', default='plots')
parser.add_argument('-o', '--output', type=str, required=False, help='Name to put in output filenames', default='output')
parser.add_argument('--g-min', type=float, required=False, help='Minimum gluino mass', default=800)
parser.add_argument('--g-max', type=float, required=False, help='Maximum gluino mass', default=2500)
parser.add_argument('--l-min', type=float, required=False, help='Minimum LSP mass', default=0)
parser.add_argument('--l-max', type=float, required=False, help='Maximum LSP mass', default=1500)
parser.add_argument('--bin-size', type=float, required=False, help='Size of bins to use', default=100)
parser.add_argument('--x-dim', type=float, required=False, help='x-dimension of figure', default=800)
parser.add_argument('--y-dim', type=float, required=False, help='y-dimension of figure', default=600)
parser.add_argument('--top-mass', type=float, required=False, help='Mass of top quark [GeV]. Mainly meant to draw exclusion line.', default=173.34)
parser.add_argument('--do-run1', action='store_true', help='Add Run-1 line to graph')
parser.add_argument('--run1-color', type=int, required=False, help='Color of Run-1 line', default=46)
parser.add_argument('--run1-excl', type=str, required=False, help='CSV file containing Run-1 exclusion points', default='run1_limit.csv')
parser.add_argument('--run1-1sigma', type=str, required=False, help='CSV file containing Run-1 exclusion (+1 sigma) points', default='run1_limit_1sigma.csv')
parser.add_argument('-b', '--batch', dest='batch_mode', action='store_true', help='Enable batch mode for ROOT.')

# parse the arguments, throw errors if missing any
args = parser.parse_args()

def get_cut_value(args, cut, cut_hash, pivotIndex = 0):
  filename = os.path.join(args.outputHash, '{0}.json'.format(cut_hash))
  if not os.path.exists(filename): return 0
  val = 0
  with open(filename) as f:
    cuts = json.load(f)
    found_cut = False
    for entry in cuts:
      if entry['selections'] == cut:
        found_cut = True
        break
    if found_cut:
      val = entry['pivot'][pivotIndex]
    else:
      print 'Did not find cut '+cut+' in hash file'
      val = -1
  return val

def nbinsx(args):
    return int((args.g_max - args.g_min) / args.bin_size)

def nbinsy(args):
    return int((args.l_max - args.l_min) / args.bin_size)

def init_canvas(args):

    #gStyle.SetPalette(1);

    c = ROOT.TCanvas("c", "", 0, 0, args.x_dim, args.y_dim)
    c.SetRightMargin(0.16)
    c.SetTopMargin(0.07)

    return c

def axis_labels(args,cut):

    return ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % cut

def init_hist(args, supercut, pivotIndex = 0):
    numPivots = len(supercut['st3'])
    formattedCut = supercut['selections'].format(*(['#']*pivotIndex + ['?'] + ['#']*(numPivots - 1 - pivotIndex)))
    return ROOT.TH2F("grid",
                axis_labels(args,formattedCut),
                nbinsx(args),
                args.g_min,
                args.g_max,
                nbinsy(args),
                args.l_min,
                args.l_max)

def draw_hist(hist):
    hist.SetMarkerSize(800)
    hist.SetMarkerColor(ROOT.kWhite)
    #gStyle.SetPalette(51)
    ROOT.gStyle.SetPaintTextFormat("0.0f");
    hist.Draw("TEXT45 COLZ")

def draw_labels(lumi):
    txt = ROOT.TLatex()
    txt.SetNDC()
    txt.DrawText(0.32,0.87,"Internal")
    txt.DrawText(0.2,0.82,"Simulation")
    #txt.SetTextSize(0.030)
    txt.SetTextSize(18)
    txt.DrawLatex(0.16,0.95,"#tilde{g}-#tilde{g} production, #tilde{g} #rightarrow t #bar{t} + #tilde{#chi}^{0}_{1}")
    txt.DrawLatex(0.62,0.95,"L_{int} = %d fb^{-1}, #sqrt{s} = 13 TeV"% lumi)
    txt.SetTextFont(72)
    txt.SetTextSize(0.05)
    txt.DrawText(0.2,0.87,"ATLAS")
    txt.SetTextFont(12)
    txt.SetTextAngle(38)
    txt.SetTextSize(0.02)
    txt.DrawText(0.33,0.63,"Kinematically Forbidden")

def draw_text(path):

    if path is None:
        return

    txt = ROOT.TLatex()
    txt.SetNDC()
    txt.SetTextSize(0.030)

    with open(path,'r') as f:
        reader = csv.reader(f,delimiter=",")
        for row in reader:
            txt.DrawLatex(float(row[0]), float(row[1]), row[2])

def draw_line(topmass=173.34):
  l=ROOT.TLine(1000,1000,2000,2000)
  l.SetLineStyle(2)
  l.DrawLine(args.g_min,args.g_min-2*topmass,args.l_max+2*topmass,args.l_max)

from array import *
def exclusion():
  x = array('d',[1400,1600,1600,1400])
  y = array('d',[600,600,800,600])
  p=TPolyLine(4,x,y)
  p.SetFillColor(1)
  p.SetFillStyle(3001)
  #p.DrawPolyLine(4,x,y)
  return p

if __name__ == '__main__':
  import ROOT
  ROOT.gROOT.SetBatch(args.batch_mode)

  import utils
  import numpy as np

  from rootpy.plotting.style import set_style, get_style
  atlas = get_style('ATLAS')
  atlas.SetPalette(51)
  set_style(atlas)

  summary = json.load(file(args.summary))

  plot_array={'sig':      [r['significance'] for r in summary],
              'signal':   [r['signal'] for r in summary],
              'bkgd':     [r['bkgd'] for r in summary],
              'mgluino':  [r['m_gluino'] for r in summary],
              'mlsp':     [r['m_lsp'] for r in summary],
              'ratio':    [r['ratio'] for r in summary]}

  # load in supercuts
  with open(args.supercuts) as f:
    supercuts = json.load(f)

  i = 0
  for supercut in supercuts:
    if supercut.get('pivot') is not None: continue
    cut = supercut['selections']
    # a cut string can have multiple pivots, need to draw a histogram for each pivot subsection
    numPivots = len(supercut['st3'])
    for pivotIndex in range(numPivots):
      print(i, cut)
      c = init_canvas(args)
      hist = init_hist(args, supercut, pivotIndex)

      for r in summary:
        g = r['m_gluino']
        l = r['m_lsp']
        z = int(round(get_cut_value(args, cut, r['hash'], pivotIndex)))
        b = hist.FindFixBin(g,l)
        xx=ROOT.Long(0)
        yy=ROOT.Long(0)
        zz=ROOT.Long(0)
        hist.GetBinXYZ(b,xx,yy,zz)
        z_old =  hist.GetBinContent(xx,yy)
        newz = max(z_old,z)
        hist.SetBinContent(b,newz)
        if newz == 0:
          hist.SetBinContent(b, 0.001)

      st3 = supercut['st3'][pivotIndex]
      # number of steps
      nSteps = len(np.arange(*st3))
      hist.GetZaxis().SetRangeUser(st3[0], st3[1])
      hist.GetZaxis().CenterLabels()
      hist.GetZaxis().SetTickLength(0)
      hist.SetContour(nSteps)
      hist.GetZaxis().SetNdivisions(nSteps, False)

      draw_hist(hist)
      draw_labels(args.lumi)
      draw_text(args.text_file)
      draw_line(args.top_mass)
      #p = exclusion()
      #p.Draw()

      if numPivots == 1:
        savefilename = args.out_directory + '/' + args.output + '_' + str(i)
      else:
        savefilename = args.out_directory + '/' + args.output + '_' + str(i) + '-' + str(pivotIndex)

      for ext in ['pdf']:
        c.SaveAs(savefilename+'.{0}'.format(ext))
      print 'Saving file ' + savefilename
    i += 1
  print 'Done'

  exit(0)

