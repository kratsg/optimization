#!/usr/bin/env python
# -*- coding: utf-8 -*-,
from __future__ import absolute_import
from __future__ import print_function

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import csv
import numpy as np

def init_palette():
  from rootpy.plotting.style import set_style, get_style
  atlas = get_style('ATLAS')
  atlas.SetPalette(51)
  set_style(atlas)
  return True

def nbins(start, stop, step):
    return abs(int( (stop - start) / step ))

def init_canvas(x, y, name="c", topMargin=0.07, rightMargin=0.16):
    c = ROOT.TCanvas("c", "", 0, 0, x, y)
    c.SetTopMargin(topMargin)
    c.SetRightMargin(rightMargin)
    return c

def axis_labels(x_label="m(#tilde{g}) [GeV]", y_label="m(#tilde{#chi}^{0}_{1}) [GeV]", z_label="", title=""):
    return ';'.join([title, x_label, y_label, z_label])

def init_hist(label, x_min, x_max, y_min, y_max, x_bin_size, y_bin_size, name="grid"):
    return ROOT.TH2F(name,
                axis_labels(z_label=label),
                nbins(x_min, x_max, x_bin_size),
                x_min,
                x_max,
                nbins(y_min, y_max, y_bin_size),
                y_min,
                y_max)

def fill_hist(hist,plot_array,label,skipNegativeSig=True):

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

def draw_hist(hist, nSigs=1, markercolor=0, drawOpts="TEXT45 COLZ", markerSize=800):
    hist.SetMarkerSize(markerSize)
    hist.SetMarkerColor(markercolor)
    #gStyle.SetPalette(51)
    ROOT.gStyle.SetPaintTextFormat("1.{0:d}f".format(nSigs));
    hist.Draw(drawOpts)

def draw_labels(lumi, label="#tilde{g}#kern[0.1]{#tilde{g}} production, #tilde{g} #rightarrow t#bar{t} + #tilde{#chi}^{0}_{1}, m(#tilde{q}) >> m(#tilde{g})", internal=True, simulation=True):
    txt = ROOT.TLatex()
    txt.SetNDC()
    if internal != simulation:  # this is xor
      txt.DrawText(0.325,0.87,"Internal" if internal else "Simulation")
    if internal and simulation:
      txt.DrawText(0.325,0.87,"Simulation")
      txt.DrawText(0.5,0.87,"Internal")

    #txt.SetTextSize(0.030)
    txt.SetTextSize(18)
    txt.DrawLatex(0.16,0.95,label)
    txt.DrawLatex(0.62,0.95,"#sqrt{{s}} = 13 TeV, {0:0.1f} fb^{{-1}}".format(lumi))
    txt.SetTextFont(72)
    txt.SetTextSize(0.05)
    txt.DrawText(0.2,0.87,"ATLAS")

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

def draw_line(x_min, y_min, x_max, y_max, topmass=173.34):
  l=ROOT.TLine(1000,1000,2000,2000)
  l.SetLineStyle(2)
  if x_min - 2*topmass > y_min:
    line_min_x = x_min
    line_min_y = x_min-2*topmass
  else:
    line_min_x = y_min + 2*topmass
    line_min_y = y_min

  if x_max - 2*topmass > y_max:
    line_max_x = y_max + 2*topmass
    line_max_y = y_max
  else:
    line_max_x = x_max
    line_max_y = x_max - 2*topmass

  l.DrawLine(line_min_x, line_min_y, line_max_x, line_max_y)
  # slope should be one as it's: LSP < Gluino - 2*topmass
  slope = float(line_max_y - line_min_y)/(line_max_x - line_min_x)

  # Draw Kinematically Forbidden as well
  txt = ROOT.TLatex()
  #txt.SetNDC()
  txt.SetTextFont(12)
  txt.SetTextAngle(np.degrees(np.arctan(slope)))
  txt.SetTextSize(0.02)
  txt.DrawText((line_max_x+line_min_x)/2., (line_max_x+line_min_x)/2. - 2*topmass + 125, "Kinematically Forbidden")


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

def get_run2(filename,linestyle,linewidth,linecolor):
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

def draw_run2_text(color):
    txt = ROOT.TLatex()
    txt.SetNDC()
    txt.SetTextAngle(45)
    txt.SetTextFont(22)
    txt.SetTextSize(0.04)
    txt.SetTextColor(color)
    txt.DrawText(0.35,0.35,"Run 2 Limit")

def exclusion():
  x = array('d',[1400,1600,1600,1400])
  y = array('d',[600,600,800,600])
  p=ROOT.TPolyLine(4,x,y)
  p.SetFillColor(1)
  p.SetFillStyle(3001)
  #p.DrawPolyLine(4,x,y)
  return p
