#!/bin/env python2

import optparse,csv,sys
sys.argv.append("-b")
from ROOT import *
import rootpy as rpy
from rootpy.plotting.style import set_style, get_style

set_style('ATLAS')
sys.argv = sys.argv[:-1]

topmass = 173.34

def parse_argv():

    parser = optparse.OptionParser()
    parser.add_option("--lumi", help="luminosity", default=5, type=int)
    parser.add_option("--z-label", help="z axis title", default="total signal event weights")
    parser.add_option("--text-file", help="text csv file", default=None, type=str)
    parser.add_option("--out", help="outfile path", default="plots/output_25ns_l5_small.pdf")
    parser.add_option("--g-min", help="min gluino mass", default=800, type=float)
    parser.add_option("--g-max", help="max gluino mass", default=2000, type=float)
    parser.add_option("--l-min", help="min lsp mass", default=0, type=float)
    parser.add_option("--l-max", help="max lsp mass", default=1300, type=float)
    parser.add_option("--bin-width", help="bin width", default=100, type=float)
    parser.add_option("--x-dim", help="x dimension of figure", default=800, type=float)
    parser.add_option("--y-dim", help="y dimension of figure", default=600, type=float)
    parser.add_option("--sigdir", help="directory where significances files are located", default='significances', type=str)

    (options,args) = parser.parse_args()

    return (options)

import csv,glob,re,json
def get_significances(opts):
  mdict = {}
  with open('mass_windows.txt', 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    m = list(reader)
    mdict = {l[0]: [l[1],l[2],l[3]] for l in m}

  def masses(did):
    mlist = mdict[did]
    mglue = mlist[0]
    mstop = mlist[1]
    mlsp = mlist[2]
    return mglue,mstop,mlsp

  filenames = glob.glob(opts.sigdir+'/s*.b*.json')
  regex = re.compile(opts.sigdir+'/s(\d{6}).b.*.json')
  dids = []
  sigs = []
  for filename in filenames:
    with open(filename) as json_file:
      sig_dict = json.load(json_file)
      entry = sig_dict[0]
      max_sig = entry['significance_scaled']
      sigs.append(max_sig)
      did = regex.search(filename)
      dids.append(did.group(1))

  plot_array=[]
  for did,sig in zip(dids,sigs):
    mgluino,mstop,mlsp = masses(did)
    row = [mgluino,mlsp,sig]
    plot_array.append(row)

  return plot_array

def nbinsx(opts):
    return int((opts.g_max - opts.g_min) / opts.bin_width)

def nbinsy(opts):
    return int((opts.l_max - opts.l_min) / opts.bin_width)

def init_canvas(opts):

    gStyle.SetPalette(1);

    c = TCanvas("c", "", 0, 0, opts.x_dim, opts.y_dim) 
    c.SetRightMargin(0.16)
    c.SetTopMargin(0.07)

    return c

def axis_labels(opts):

    return ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % opts.z_label

def init_hist(opts):
    return TH2F("grid", 
                axis_labels(opts), 
                nbinsx(opts), 
                opts.g_min, 
                opts.g_max, 
                nbinsy(opts), 
                opts.l_min, 
                opts.l_max)

def fill_hist(hist,opts):

  plot_array = get_significances(opts)
  for row in plot_array:
      g = int(row[0])
      l = int(row[1])
      z = row[2]
      if(z>0):
        #hist.Fill(g,l,z)
        b = hist.FindFixBin(g,l)
        hist.SetBinContent(b,z)
        '''x=Long(0)
        y=Long(0)
        z=Long(0)
        hist.GetBinXYZ(b,x,y,z)
        print hist.GetBinContent(x,y)'''
      else:
        hist.Fill(g,l,0.01)

def draw_hist(hist):
    hist.SetMarkerSize(1.5)
    hist.SetMarkerColor(kWhite)
    gStyle.SetPalette(51)
    gStyle.SetPaintTextFormat("1.1f");
    hist.Draw("TEXT COLZ")

def draw_labels(lumi):
    txt = TLatex()
    txt.SetNDC()
    txt.DrawText(0.32,0.87,"Internal")
    txt.DrawText(0.2,0.82,"Simulation")
    txt.SetTextSize(0.030)
    txt.DrawLatex(0.16,0.95,"#tilde{g}-#tilde{g} production, #tilde{g} #rightarrow t #bar{t} + #tilde{#chi}^{0}_{1}")
    txt.DrawLatex(0.62,0.95,"#int L dt = %d fb^{-1}, #sqrt{s} = 13 TeV"% lumi)
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

    opts = parse_argv()
    c = init_canvas(opts)
    h = init_hist(opts)
    fill_hist(h,opts)
    draw_hist(h)
    draw_labels(opts.lumi)
    draw_text(opts.text_file)
    draw_line()
    #p = exclusion()
    #p.Draw()
    c.SaveAs(opts.out)

    exit(0)

