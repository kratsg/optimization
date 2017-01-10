from root_optimize import plotting
import os

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

  #plotting.init_palette()

  import json
  summary = json.load(file(args.summary))

  plot_array={'sig':      [r['significance'] for r in summary],
              'signal':   [r['signal'] for r in summary],
              'bkgd':     [r['bkgd'] for r in summary],
              'mgluino':  [r['m_gluino'] for r in summary],
              'mlsp':     [r['m_lsp'] for r in summary],
              'ratio':    [r['ratio'] for r in summary]}

  c = plotting.init_canvas(args.x_dim, args.y_dim)
  labels = ['sig','signal','bkgd', 'ratio']
  zlabels = ['Significance in optimal cut','Exp. num. signal in optimal cut','Exp. num. bkgd in optimal cut', 'Signal/Background']
  nSigs = [2, 3, 3, 2]
  for label,zlabel,nSig in zip(labels,zlabels,nSigs):
    h = plotting.init_hist(zlabel, args.g_min, args.g_max, args.l_min, args.l_max, args.bin_size)
    plotting.fill_hist(h,plot_array,label, label=='sig')
    levels = np.linspace(-10, 10, 255, dtype=np.double)
    levels[0] = np.finfo('d').min
    levels[-1] = np.finfo('d').max
    h.SetContour(254, levels)

    plotting.draw_hist(h, nSig)
    plotting.draw_labels(args.lumi)
    plotting.draw_text(args.text_file)
    plotting.draw_line(args.g_min, args.g_max, args.l_max, args.top_mass)
    savefilename = os.path.join(args.out_directory, '_'.join([args.output, label]))
    if args.do_run1:
      gr = plotting.get_run1(args.run1_excl,1,3,args.run1_color)
      gr.Draw("C")
      gr_1sigma = plotting.get_run1(args.run1_1sigma,3,1,args.run1_color)
      gr_1sigma.Draw("C")
      plotting.draw_run1_text(args.run1_color)
      savefilename += "_wrun1"
    #p = exclusion()
    #p.Draw()
    c.SaveAs(savefilename + ".pdf")
    print "Saving file " + savefilename
    c.Clear()

  exit(0)
