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
    parser.add_option("--text-file", help="text csv file", default=None, type=str)
    parser.add_option("--outdir", help="outfile directory", default="plots")
    parser.add_option("--g-min", help="min gluino mass", default=800, type=float)
    parser.add_option("--g-max", help="max gluino mass", default=2000, type=float)
    parser.add_option("--l-min", help="min lsp mass", default=0, type=float)
    parser.add_option("--l-max", help="max lsp mass", default=1300, type=float)
    parser.add_option("--bin-width", help="bin width", default=100, type=float)
    parser.add_option("--x-dim", help="x dimension of figure", default=800, type=float)
    parser.add_option("--y-dim", help="y dimension of figure", default=600, type=float)
    parser.add_option("--sigdir", help="directory where significances files are located", default='significances', type=str)
    parser.add_option("--hashdir", help="directory where hash files are located", default='outputHash', type=str)
    parser.add_option("--tag", help="tag of supercuts", default="")

    (options,args) = parser.parse_args()

    return (options)
import pdb
import csv,glob,re,json
def get_cut_value(opts,cut):
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

  filenames = glob.glob(opts.sigdir+'_'+opts.tag+'/s*.b*.json')
  regex = re.compile(opts.sigdir+'_'+opts.tag+'/s(\d{6}).b.*.json')
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
  
  def get_value(opts,cut,h):
    filenames = glob.glob(opts.hashdir+'_'+opts.tag+'/'+h+'.json')
    filename = filenames[0]
    val = 0
    with open(filename) as json_file:
      cuts_dict = json.load(json_file)
      for entry in cuts_dict:
        if entry['branch'] == cut: break
      val = entry['pivot']
    return val


  plot_array=[]
  for did,h in zip(dids,hashs):
    mgluino,mstop,mlsp = masses(did)
    val = get_value(opts,cut,h)
    row = [mgluino,mlsp,val]
    if int(mstop) == 5000: plot_array.append(row)

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

def axis_labels(opts,cut):

    return ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % cut

def init_hist(opts,cut):
    return TH2F("grid", 
                axis_labels(opts,cut), 
                nbinsx(opts), 
                opts.g_min, 
                opts.g_max, 
                nbinsy(opts), 
                opts.l_min, 
                opts.l_max)
import pdb
def fill_hist(hist,opts,cut):

  plot_array = get_cut_value(opts,cut)
  for row in plot_array:
      g = int(row[0])
      l = int(row[1])
      z = int(round(row[2]))
      b = hist.FindFixBin(g,l)
      if z>0:
        xx=Long(0)
        yy=Long(0)
        zz=Long(0)
        hist.GetBinXYZ(b,xx,yy,zz)
        z_old =  hist.GetBinContent(xx,yy)
        newz = max(z_old,z)
        hist.SetBinContent(b,newz)
      else:
        hist.SetBinContent(b,-1)


def draw_hist(hist):
    hist.SetMarkerSize(1.0)
    hist.SetMarkerColor(kWhite)
    gStyle.SetPalette(51)
    gStyle.SetPaintTextFormat("1.11g");
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

    cuts = ['m_effective','met','multiplicity_jet','multiplicity_jet_b','multiplicity_topTag_loose']
    opts = parse_argv()
    for cut in cuts:
      c = init_canvas(opts)
      h = init_hist(opts,cut)
      fill_hist(h,opts,cut)
      draw_hist(h)
      draw_labels(opts.lumi)
      draw_text(opts.text_file)
      draw_line()
      #p = exclusion()
      #p.Draw()
      c.SaveAs(opts.outdir + '/output_' + opts.tag + '_' + cut + '.pdf')

    exit(0)

