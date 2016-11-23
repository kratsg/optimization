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
      g = int(plot_array['mgluino'][i])
      l = int(plot_array['mlsp'][i])
      z = plot_array[label][i]
      sig = plot_array['sig'][i]
      b = hist.FindFixBin(g,l)
      if(sig>0) or not(skipNegativeSig):
        xx=ROOT.Long(0)
        yy=ROOT.Long(0)
        zz=ROOT.Long(0)
        hist.GetBinXYZ(b,xx,yy,zz)
        z_old =  hist.GetBinContent(xx,yy)
        newz = max(z_old,z) #for significances this makes sense. For the other quantities not so much. Oh well.
        hist.SetBinContent(b,newz)
      else:
        hist.SetBinContent(b,0.01)

def draw_hist(hist, nSigs=1):
    hist.SetMarkerSize(800)
    hist.SetMarkerColor(ROOT.kWhite)
    #gStyle.SetPalette(51)
    ROOT.gStyle.SetPaintTextFormat("1.{0:d}f".format(nSigs));
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

    txt = TLatex()
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
  x = array('d',[1400,1600,1600,1400])
  y = array('d',[600,600,800,600])
  p=ROOT.TPolyLine(4,x,y)
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

  parser = argparse.ArgumentParser(description='Author: A. Cukierman, G. Stark. v.{0}'.format(__version__),
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))
  parser.add_argument('--summary', type=str, required=True, help='Summary json')
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

  import ROOT
  ROOT.gROOT.SetBatch(args.batch_mode)

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

  c = init_canvas(args)
  labels = ['sig','signal','bkgd', 'ratio']
  ylabels = ['Significance in optimal cut','Exp. num. signal in optimal cut','Exp. num. bkgd in optimal cut', 'Signal/Background']
  nSigs = [2, 3, 3, 2]
  for label,ylabel,nSig in zip(labels,ylabels,nSigs):
    h = init_hist(args,ylabel)
    fill_hist(h,args,plot_array,label, label=='sig')
    draw_hist(h, nSig)
    draw_labels(args.lumi)
    draw_text(args.text_file)
    draw_line(args.top_mass)
    savefilename = os.path.join(args.out_directory, '_'.join([args.output, label]))
    if args.do_run1:
      gr = get_run1(args.run1_excl,1,3,args.run1_color)
      gr.Draw("C")
      gr_1sigma = get_run1(args.run1_1sigma,3,1,args.run1_color)
      gr_1sigma.Draw("C")
      draw_run1_text(args.run1_color)
      savefilename += "_wrun1"
    #p = exclusion()
    #p.Draw()
    c.SaveAs(savefilename + ".pdf")
    print "Saving file " + savefilename
    c.Clear()

  exit(0)

