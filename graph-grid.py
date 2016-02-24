#!/bin/env python2

import optparse,csv,sys
sys.argv.append("-b")
from ROOT import *
import rootpy as rpy
from rootpy.plotting.style import set_style, get_style
import os

atlas = get_style('ATLAS')
atlas.SetPalette(51)
set_style(atlas)
sys.argv = sys.argv[:-1]

topmass = 173.34

def parse_argv():

    parser = optparse.OptionParser()
    parser.add_option("--lumi", help="luminosity", default=5, type=int)
    #parser.add_option("--z-label", help="z axis title", default="significance in optimal cut")
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
    parser.add_option("--run1_color", help="color of run 1 line", default=46, type=int)
    parser.add_option("--dorun1", help="add run 1 line to graph", default=True)
    parser.add_option("--run1_csvfile", help="csv file containing run 1 exclusion points", default="run1_limit.csv", type=str)
    parser.add_option("--run1_1sigma_csvfile", help="csv file containing run 1 exclusion (+1 sigma) points", default="run1_limit_1sigma.csv", type=str)
    parser.add_option("--sigdir", help="directory where significances files are located", default='significances', type=str)
    parser.add_option("--cutdir", help="directory where cuts files are located", default='cuts', type=str)

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

  regex = re.compile(r'{0:s}'.format(os.path.join(opts.sigdir, 's(\d+)\.b([a-fA-F\d]{32})\.json')))
  dids = []
  sigs = []
  signals = []
  bkgds = []
  ratios = []
  for filename in filenames:
    with open(filename) as json_file:
      sig_dict = json.load(json_file)
      entry = sig_dict[0]
      max_sig = entry['significance_scaled']
      max_hash = entry['hash']

      did = regex.search(filename)
      signal_did = did.group(1)
      with open(opts.cutdir+'/'+signal_did+'.json') as signal_json_file:
        signal_dict = json.load(signal_json_file)
        entry = signal_dict[max_hash]
        signal = entry['scaled']*opts.lumi*1000
      with open(os.path.join(opts.sigdir, '{0:s}.json'.format(did.group(2))), 'r') as f:
        bkgd_dids = json.load(f)
      bkgd = 0
      for bkgd_did in bkgd_dids:
        with open(opts.cutdir+'/'+bkgd_did+'.json') as bkgd_json_file:
          bkgd_dict = json.load(bkgd_json_file)
          entry = bkgd_dict[max_hash]
          bkgd += entry['scaled']*opts.lumi*1000

      sigs.append(max_sig)
      signals.append(signal)
      bkgds.append(bkgd)
      try:
         ratios.append(signal/bkgd)
      except:
         ratios.append(-1)
      dids.append(signal_did)


  plot_array={'sig':[],'signal':[],'bkgd':[],'mgluino':[],'mlsp':[],'ratio':[]}
  for did,sig,signal,bkgd,ratio in zip(dids,sigs,signals,bkgds,ratios):
    mgluino,mstop,mlsp = masses(did)
    if int(mstop) == 5000:
      plot_array['sig'].append(sig)
      plot_array['signal'].append(signal)
      plot_array['bkgd'].append(bkgd)
      plot_array['ratio'].append(ratio)
      plot_array['mgluino'].append(mgluino)
      plot_array['mlsp'].append(mlsp)

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

def axis_labels(opts,label):
    return ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % label

def init_hist(opts,label):
    return TH2F("grid",
                axis_labels(opts,label),
                nbinsx(opts),
                opts.g_min,
                opts.g_max,
                nbinsy(opts),
                opts.l_min,
                opts.l_max)

def fill_hist(hist,opts,plot_array,label,skipNegativeSig=True):

  for i in range(len(plot_array[label])):
      g = int(plot_array['mgluino'][i])
      l = int(plot_array['mlsp'][i])
      z = plot_array[label][i]
      sig = plot_array['sig'][i]
      b = hist.FindFixBin(g,l)
      if(sig>0) or not(skipNegativeSig):
        xx=Long(0)
        yy=Long(0)
        zz=Long(0)
        hist.GetBinXYZ(b,xx,yy,zz)
        z_old =  hist.GetBinContent(xx,yy)
        newz = max(z_old,z) #for significances this makes sense. For the other quantities not so much. Oh well.
        hist.SetBinContent(b,newz)
      else:
        hist.SetBinContent(b,0.01)

def draw_hist(hist, nSigs=1):
    hist.SetMarkerSize(800)
    hist.SetMarkerColor(kWhite)
    #gStyle.SetPalette(51)
    gStyle.SetPaintTextFormat("1.{0:d}f".format(nSigs));
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
def get_run1(filename,linestyle,linewidth,linecolor):
  x = array('f')
  y = array('f')
  n = 0
  with open(filename,'r') as csvfile:
    reader = csv.reader(csvfile, delimiter = ' ')
    for row in reader:
      n += 1
      x.append(float(row[0]))
      y.append(float(row[1]))

  gr = TGraph(n,x,y)
  gr.SetLineColor(linecolor)
  gr.SetLineWidth(linewidth)
  gr.SetLineStyle(linestyle)
  return gr

def draw_run1_text(color):
    txt = TLatex()
    txt.SetNDC()
    txt.SetTextFont(22)
    txt.SetTextSize(0.04)
    txt.SetTextColor(color)
    txt.DrawText(0.2,0.2,"Run 1 Limit")

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
    plot_array = get_significances(opts)
    c = init_canvas(opts)
    labels = ['sig','signal','bkgd', 'ratio']
    ylabels = ['Significance in optimal cut','Exp. num. signal in optimal cut','Exp. num. bkgd in optimal cut', 'Signal/Background']
    nSigs = [2, 3, 3, 2]
    for label,ylabel,nSig in zip(labels,ylabels,nSigs):
      h = init_hist(opts,ylabel)
      fill_hist(h,opts,plot_array,label, label=='sig')
      draw_hist(h, nSig)
      draw_labels(opts.lumi)
      draw_text(opts.text_file)
      draw_line()
      savefilename = opts.outdir + "/" + opts.outfilebase + "_" + label
      if opts.dorun1:
        gr = get_run1(opts.run1_csvfile,1,3,opts.run1_color)
        gr.Draw("C")
        gr_1sigma = get_run1(opts.run1_1sigma_csvfile,3,1,opts.run1_color)
        gr_1sigma.Draw("C")
        draw_run1_text(opts.run1_color)
        savefilename += "_wrun1"
      #p = exclusion()
      #p.Draw()
      c.SaveAs(savefilename + ".pdf")
      print "Saving file " + savefilename
      c.Clear()

    exit(0)

