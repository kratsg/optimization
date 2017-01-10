import os
import csv
import json

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

def axis_labels(args,label):
    return ";m_{#tilde{g}} [GeV]; m_{#tilde{#chi}^{0}_{1}} [GeV];%s" % label

def init_hist(args,label):
    return ROOT.TH2F("grid",
                axis_labels(args,label),
                nbinsx(args),
                args.g_min,
                args.g_max,
                nbinsy(args),
                args.l_min,
                args.l_max)

def fill_hist(hist,args,plot_array,label,skipNegativeSig=True):

  for i in range(len(plot_array[label])):
      g = int(plot_array['m_gluino'][i])
      l = int(plot_array['m_lsp'][i])
      z = plot_array[label][i]
      sig = plot_array['significance'][i]
      b = hist.FindFixBin(g,l)
      #if(sig>0) or not(skipNegativeSig):
      xx=ROOT.Long(0)
      yy=ROOT.Long(0)
      zz=ROOT.Long(0)
      hist.GetBinXYZ(b,xx,yy,zz)
      hist.SetBinContent(b,z)
      #h.SetMinimum(-2.0)
      #h.SetMaximum(2.0)
      levels = np.linspace(-1, 1, 255, dtype=np.double)
      levels[0] = np.finfo('d').min
      levels[-1] = np.finfo('d').max
      h.SetContour(254, levels)

def draw_hist(hist, nSigs=1, markercolor=0, drawOpts="TEXT45 COLZ"):
    # hist.SetMaximum(args.histmax)
    # hist.SetMinimum(args.histmin)
    hist.SetMarkerSize(600)
    hist.SetMarkerColor(markercolor)
    #ROOT.gStyle.SetPalette(51)
    ROOT.gStyle.SetPaintTextFormat("1.{0:d}f".format(nSigs));
    hist.Draw(drawOpts)

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
  if args.g_max - 2*topmass > args.l_max:
    l.DrawLine(args.g_min, args.g_min-2*topmass, args.l_max+2*topmass, args.l_max)
  else:
    l.DrawLine(args.g_min,args.g_min-2*topmass,args.g_max,args.g_max-2*topmass)

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

  gr = ROOT.TGraph(n,x,y)
  gr.SetLineColor(linecolor)
  gr.SetLineWidth(linewidth)
  gr.SetLineStyle(linestyle)
  return gr

def draw_run1_text(color):
    txt = ROOT.TLatex()
    txt.SetNDC()
    txt.SetTextFont(22)
    txt.SetTextSize(0.04)
    txt.SetTextColor(color)
    txt.DrawText(0.2,0.2,"Run 1 Limit")

def exclusion():
  #x = array('d',[args.g_min,args.l_max+2*topmass,args.g_min])
  #y = array('d',[args.g_min-2*topmass,args.l_max,args.l_max])
  x = array('d',[1400,1600,1600,1400])
  y = array('d',[600,600,800,600])
  p=TPolyLine(4,x,y)
  p.SetFillColor(1)
  p.SetFillStyle(3001)
  #p.DrawPolyLine(4,x,y)
  return p

if __name__ == '__main__':

  import argparse
  import subprocess

  class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    pass

  __version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
  __short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

  parser = argparse.ArgumentParser(description='Author: N. Harrison, G. Stark. v.{0}'.format(__version__),
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  parser.add_argument('--base-summary', type=str, required=True, help='Base summary json')
  parser.add_argument('--comp-summary', type=str, required=True, help='Summary to compare with base json')
  parser.add_argument('--lumi', type=float, required=False, help='Luminosity to write on plot [ifb]', default=35)
  parser.add_argument('--text-file', type=str, required=False, help='text csv file', default=None)
  parser.add_argument('--out-directory', type=str, required=False, help='output directory', default='plots')
  parser.add_argument('-o', '--output', type=str, required=False, help='Name to put in output filenames', default='output')
  parser.add_argument('--g-min', type=float, required=False, help='Minimum gluino mass', default=200)
  parser.add_argument('--g-max', type=float, required=False, help='Maximum gluino mass', default=2500)
  parser.add_argument('--l-min', type=float, required=False, help='Minimum LSP mass', default=0)
  parser.add_argument('--l-max', type=float, required=False, help='Maximum LSP mass', default=2300)
  parser.add_argument('--bin-size', type=float, required=False, help='Size of bins to use', default=100)
  parser.add_argument('--x-dim', type=float, required=False, help='x-dimension of figure', default=800)
  parser.add_argument('--y-dim', type=float, required=False, help='y-dimension of figure', default=600)
  parser.add_argument('--top-mass', type=float, required=False, help='Mass of top quark [GeV]. Mainly meant to draw exclusion line.', default=173.34)
  parser.add_argument('-b', '--batch', dest='batch_mode', action='store_true', help='Enable batch mode for ROOT.')

  # parse the arguments, throw errors if missing any
  args = parser.parse_args()

  import ROOT
  ROOT.PyConfig.IgnoreCommandLineOptions = True
  ROOT.gROOT.SetBatch(args.batch_mode)

  from rootpy.plotting.style import set_style, get_style
  atlas = get_style('ATLAS')
  atlas.cd()
  ROOT.gStyle.SetPalette(51)

  # based on kDeepSea, kCherry (https://root.cern.ch/doc/v606/TColor_8cxx_source.html#l01672)

  import numpy as np
  NCont = 255
  stops = np.linspace(0.0, 1.0, 11, dtype=np.double)

  kDeepSea = {'red':   [ 24./255.,  32./255.,  27./255.,  25./255.,  29./255.],
              'green': [ 37./255.,  74./255., 113./255., 160./255., 221./255. ],
              'blue':  [  98./255., 129./255., 154./255., 184./255., 221./255. ]}

  kCherry = {'red':    [ 188./255., 196./255., 214./255., 223./255., 235./255., 255./255. ],
             'green':  [  37./255.,  67./255.,  91./255., 132./255., 185./255., 255./255. ],
             'blue':   [  45./255.,  66./255.,  98./255., 137./255., 187./255., 255./255. ]}

  palette = {'red': kCherry['red']+kDeepSea['red'][::-1],
             'green': kCherry['green']+kDeepSea['green'][::-1],
             'blue': kCherry['blue']+kDeepSea['blue'][::-1]}

  p = ROOT.TColor.CreateGradientColorTable(len(stops), stops,
                                           np.array(palette['red'], np.double),
                                           np.array(palette['green'], np.double),
                                           np.array(palette['blue'], np.double), NCont, 1.0);
  if p == -1: raise ValueError('CreateGradientColorTable is not set-up right!')
  ROOT.gStyle.SetNumberContours(NCont)
  set_style(atlas)


  base_summary = json.load(file(args.base_summary))
  comp_summary = json.load(file(args.comp_summary))

  plot_array={'significance':      [],
              'signal':   [],
              'bkgd':     [],
              'm_gluino':  [],
              'm_lsp':     [],
              'ratio':    []}

  plot_arraylarge={'significance':      [],
              'signal':   [],
              'bkgd':     [],
              'm_gluino':  [],
              'm_lsp':     [],
              'ratio':    []}

  plot_arraysmall={'significance':      [],
              'signal':   [],
              'bkgd':     [],
              'm_gluino':  [],
              'm_lsp':     [],
              'ratio':    []}

  for base_r in base_summary:
    comp_r = next((item for item in comp_summary if item['m_gluino'] == base_r['m_gluino'] and item['m_lsp'] == base_r['m_lsp']), None)
    saveTo = plot_arraylarge
    for key in ['significance', 'signal', 'bkgd', 'ratio']:
      val = -1
      try: val = (comp_r[key] - base_r[key])/base_r[key]
      except: pass

      # set val to a little larger than 0, bins with val=0.0 are not drawn. what the fuck ROOT
      if val == 0.0: val = 0.0001
      if abs(val) < 0.15 and key == 'significance': saveTo = plot_arraysmall

      plot_array[key].append(val)
      saveTo[key].append(val)
    for key in ['m_gluino', 'm_lsp']:
      plot_array[key].append(base_r[key])
      saveTo[key].append(base_r[key])

  c = init_canvas(args)
  labels = ['significance']
  ylabels = ['Fractional Change in Significance']
  nSigs = [3]
  for label,ylabel,nSig in zip(labels,ylabels,nSigs):
    h = init_hist(args, ylabel)
    hlarge = init_hist(args, ylabel)
    hsmall = init_hist(args, ylabel)

    fill_hist(h,args,plot_array,label, label=='significance')
    fill_hist(hlarge,args, plot_arraylarge, label, label=='significance')
    fill_hist(hsmall,args, plot_arraysmall, label, label=='significance')

    draw_hist(h, nSig, ROOT.kWhite, "COLZ")
    draw_hist(hlarge, nSig, ROOT.kWhite, "TEXT45 SAME")
    draw_hist(hsmall, nSig, ROOT.kGray+2, "TEXT45 SAME")

    draw_labels(args.lumi)
    draw_text(args.text_file)
    draw_line(args.top_mass)
    savefilename = args.out_directory + "/" + args.output + "_compare_" + label
    #p = exclusion()
    #p.Draw()
    c.SaveAs(savefilename + ".pdf")
    print "Saving file " + savefilename
    c.Clear()

    exit(0)
