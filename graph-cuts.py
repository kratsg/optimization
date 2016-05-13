#!/bin/env python2

import optparse,csv,sys
sys.argv.append("-b")
from ROOT import *
import rootpy as rpy
from rootpy.plotting.style import set_style, get_style
import numpy as np
import utils
import re

atlas = get_style('ATLAS')
atlas.SetPalette(51)
set_style(atlas)
sys.argv = sys.argv[:-1]

topmass = 173.34

def parse_argv():

    parser = optparse.OptionParser()
    parser.add_option("--lumi", help="luminosity", default=5, type=int)
    parser.add_option("--text-file", help="text csv file", default=None, type=str)
    parser.add_option("--outdir", help="outfile directory", default="plots")
    parser.add_option("--outfilebase", help="outfile base name", default="output")
    parser.add_option("--g-min", help="min gluino mass", default=800, type=float)
    parser.add_option("--g-max", help="max gluino mass", default=2000, type=float)
    parser.add_option("--l-min", help="min lsp mass", default=0, type=float)
    parser.add_option("--l-max", help="max lsp mass", default=1300, type=float)
    parser.add_option("--bin-width", help="bin width", default=100, type=float)
    parser.add_option("--x-dim", help="x dimension of figure", default=800, type=float)
    parser.add_option("--y-dim", help="y dimension of figure", default=600, type=float)
    parser.add_option("--sigdir", help="directory where significances files are located", default='significances', type=str)
    parser.add_option("--hashdir", help="directory where hash files are located", default='outputHash', type=str)
    parser.add_option("--supercuts", help="supercuts file detailing all selections used", default="supercuts.json", type=str)
    parser.add_option('--massWindows', help='Location of mass windows file', default='mass_windows.txt', type=str)

    (options,args) = parser.parse_args()

    return (options)
import pdb
import csv,glob,re,json
def get_cut_value(opts, cut, pivotIndex = 0):
  masses = utils.load_mass_windows(opts.massWindows)

  filenames = glob.glob(opts.sigdir+'/s*.b*.json')
  regex = re.compile(opts.sigdir+'/s(\d{6}).b.*.json')
  dids = []
  hashs = []
  for filename in filenames:
    with open(filename) as json_file:
      hash_dict = json.load(json_file)
      entry = hash_dict[0]
      h = entry['hash']
      hashs.append(h)
      did = regex.search(filename)
      dids.append(did.group(1))

  def get_value(opts, cut, h, pivotIndex = 0):
    filenames = glob.glob(opts.hashdir+'/'+h+'.json')
    if len(filenames)==0:
      return 0
    filename = filenames[0]
    val = 0
    with open(filename) as json_file:
      cuts_dict = json.load(json_file)
      found_cut = False
      for entry in cuts_dict:
        if entry['selections'] == cut:
          found_cut = True
          break
      if found_cut:
        val = entry['pivot'][pivotIndex]
      else:
        print 'Did not find cut '+cut+' in hash file'
        val = -1
    return val


  plot_array=[]
  for did,h in zip(dids,hashs):
    mgluino,mstop,mlsp = masses.get(did)
    val = get_value(opts, cut, h, pivotIndex)
    row = [mgluino,mlsp,val]
    if int(mstop) == 5000:
      plot_array.append(row)

  return plot_array

def nbinsx(opts):
    return int((opts.g_max - opts.g_min) / opts.bin_width)

def nbinsy(opts):
    return int((opts.l_max - opts.l_min) / opts.bin_width)

def init_canvas(opts):

    #gStyle.SetPalette(1);

    c = TCanvas("c", "", 0, 0, opts.x_dim, opts.y_dim)
    c.SetRightMargin(0.16)
    c.SetTopMargin(0.07)

    return c

def axis_labels(opts,cut):

    return ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % cut

def init_hist(opts, cut, pivotIndex = 0):
    numPivots = len(set(p.findall(cut)))
    formattedCut = cut.format(*(['#']*pivotIndex + [pivotIndex] + ['#']*(numPivots - 1 - pivotIndex)))
    return TH2F("grid",
                axis_labels(opts,formattedCut),
                nbinsx(opts),
                opts.g_min,
                opts.g_max,
                nbinsy(opts),
                opts.l_min,
                opts.l_max)
import pdb
def fill_hist(hist, opts, cut, pivotIndex = 0):

  plot_array = get_cut_value(opts, cut, pivotIndex)
  for row in plot_array:
      g = int(row[0])
      l = int(row[1])
      z = int(round(row[2]))
      b = hist.FindFixBin(g,l)
      xx=Long(0)
      yy=Long(0)
      zz=Long(0)
      hist.GetBinXYZ(b,xx,yy,zz)
      z_old =  hist.GetBinContent(xx,yy)
      newz = max(z_old,z)
      hist.SetBinContent(b,newz)
      if newz == 0:
        hist.SetBinContent(b, 0.001)

def draw_hist(hist):
    hist.SetMarkerSize(800)
    hist.SetMarkerColor(kWhite)
    #gStyle.SetPalette(51)
    gStyle.SetPaintTextFormat("0.0f");
    hist.Draw("TEXT COLZ")

def draw_labels(lumi):
    txt = TLatex()
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

    txt = TLatex()
    txt.SetNDC()
    txt.SetTextSize(0.030)

    with open(path,'r') as f:
        reader = csv.reader(f,delimiter=",")
        for row in reader:
            txt.DrawLatex(float(row[0]), float(row[1]), row[2])

def draw_line():
  l=TLine(1000,1000,2000,2000)
  l.SetLineStyle(2)
  l.DrawLine(opts.g_min,opts.g_min-2*topmass,opts.l_max+2*topmass,opts.l_max)

from array import *
def exclusion():
  #x = array('d',[opts.g_min,opts.l_max+2*topmass,opts.g_min])
  #y = array('d',[opts.g_min-2*topmass,opts.l_max,opts.l_max])
  x = array('d',[1400,1600,1600,1400])
  y = array('d',[600,600,800,600])
  p=TPolyLine(4,x,y)
  p.SetFillColor(1)
  p.SetFillStyle(3001)
  #p.DrawPolyLine(4,x,y)
  return p

if __name__ == '__main__':

    #cuts = ['m_effective','mTb','met','multiplicity_jet','multiplicity_jet_b','multiplicity_topTag_loose']
    #cuts = ['m_effective','mTb','met','multiplicity_jet','multiplicity_jet_b','multiplicity_jet_largeR']
    #cuts = ['m_effective','mTb','met','multiplicity_jet','multiplicity_jet_b']

    opts = parse_argv()

    # load in supercuts
    with open(opts.supercuts) as f:
      supercuts = json.load(f)

    p = re.compile('{(\d+)}')

    i = 0
    for supercut in supercuts:
      if supercut.get('pivot') is not None: continue
      cut = supercut['selections']
      # a cut string can have multiple pivots, need to draw a histogram for each pivot subsection
      numPivots = len(supercut['st3'])
      '''
      # this is where it gets tricky, need to know how many actual format entries there are...
      numPivots = len(set(p.findall(cut)))
      '''
      for pivotIndex in range(numPivots):
        print(i, cut)
        c = init_canvas(opts)
        h = init_hist(opts, cut, pivotIndex)
        fill_hist(h, opts, cut, pivotIndex)
        st3 = supercut['st3'][pivotIndex]
        # number of steps
        nSteps = len(np.arange(*st3))
        h.GetZaxis().SetRangeUser(st3[0], st3[1])
        h.GetZaxis().CenterLabels()
        h.GetZaxis().SetTickLength(0)
        h.SetContour(nSteps)
        h.GetZaxis().SetNdivisions(nSteps, False)

        draw_hist(h)
        draw_labels(opts.lumi)
        draw_text(opts.text_file)
        draw_line()
        #p = exclusion()
        #p.Draw()

        if numPivots == 1:
          savefilename = opts.outdir + '/' + opts.outfilebase + '_' + str(i)
        else:
          savefilename = opts.outdir + '/' + opts.outfilebase + '_' + str(i) + '-' + str(pivotIndex)

        for ext in ['pdf']:
          c.SaveAs(savefilename+'.{0}'.format(ext))
        print 'Saving file ' + savefilename
      i += 1
    print 'Done'

    exit(0)

