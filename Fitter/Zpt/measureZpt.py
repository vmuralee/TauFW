#! /usr/bin/env python
# Author: Izaak Neutelings (January 2021)
# Description: Script to measure Z pt reweighting based on dimuon events
#   ./measureZpt.py -y 2018
from utils import *
from TauFW.Plotter.plot.Plot2D import Plot2D
gSystem.Load('RooUnfold/libRooUnfold.so')
from ROOT import RooUnfoldResponse, RooUnfoldBinByBin, kRed

ptitle   = "p_{T}(#mu#mu) [GeV]"
mtitle   = "m_{#mu#mu} [GeV]"
baseline = "q_1*q_2<0 && iso_1<0.15 && iso_1<0.15 && !extraelec_veto && !extramuon_veto && m_vis>20"
Zmbins0  = [20,70,91,110,150,200,300,400,500,600,700,800,900,1000]
Zmbins1  = [20,30,40,50,60,70,80,85,88,89,89.5,90,90.5,91,91.5,92,93,94,95,100,110,120,180,500,1000]
ptbins0  = [0,5,10,15,20,25,30,35,40,45,50,60,70,100,140,200,300,500,1000]
ptbins1  = [0,5,10,15,20,25,30,35,40,45,50,60,70,100,150,1000]


def measureZpt_unfold(samples,outdir='weights',plotdir=None,parallel=True,tag=""):
  """Measure Z pT weights in dimuon pT by unfolding."""
  LOG.header("measureZpt()")
  
  # SETTINGS
  hname    = 'zpt'
  rtitle   = "Reco-level weight"
  gtitle   = "Gen-level weight"
  fname    = "%s/zpt_weight_$CAT%s.root"%(outdir,tag)
  pname    = "%s/zpt_$CAT%s.png"%(plotdir or outdir,tag)
  outdir   = ensuredir(outdir) #repkey(outdir,CHANNEL=channel,ERA=era))
  logx     = True #and False
  logy     = True #and False
  logz     = True #and False
  method   = None #'QCD'
  dysample = samples.get('DY',unique=True)
  
  # SELECTIONS
  selections = [
    Sel('baseline', baseline),
    #Sel('m_{mumu} > 200 GeV',               baseline+" && m_vis>200", fname="mgt200"),
  ]
  #xvar = Var('m_ll', Zmbins, mtitle)
  xvar_reco = Var('pt_ll',  ptbins0,"Reco-level "+ptitle,cbins={'njets50==0':ptbins1})
  xvar_gen  = Var('pt_moth',ptbins0,"Gen-level "+ptitle,cbins={'njets50==0':ptbins1})
  
  for selection in selections:
    LOG.color(selection.title,col='green')
    print ">>> %s"%(selection.selection)
    xvar_reco.changecontext(selection.selection)
    xvar_gen.changecontext(selection.selection)
    fname_ = repkey(fname,CAT=selection.filename).replace('_baseline',"")
    line   = (xvar_reco.min,1.,xvar_reco.max,1.)
    
    print ">>> Unfold reco-level weights as a function of %s"%(xvar_reco.title)
    outfile = ensureTFile(fname_,'UPDATE')
    ctrldir = ensureTDirectory(outfile,"control",cd=False)
    
    # HISTOGRAMS
    hists = samples.gethists(xvar_reco,selection,split=False,blind=False,method=method,
                             signal=False,parallel=parallel)
    obshist, exphist, dyhist, bkghist = getdyhist(hname,hists,"_reco",verb=2)
    dyhist_gen = dysample.gethist(xvar_gen,selection,split=False,parallel=parallel,weight="")
    #histSF_gaps = histSF.Clone("gaps")
    #setContentRange(histSF,0.0,3.0)
    #fillTH2Gaps(histSF,axis='x')
    #setContentRange(histSF,0.2,3.0)
    #extendContent(histSF)
    
    # OBSERVED DY = DATA - BKG
    obsdyhist = obshist.Clone(hname+"_obsdy"+tag)
    obsdyhist.SetBinErrorOption(obshist.kNormal)
    obsdyhist.Add(bkghist,-1)
    
    # RESPONSE MATRIX
    resphist = dysample.gethist2D(xvar_reco,xvar_gen,selection,split=False,parallel=parallel)
    
    # UNFOLD
    print ">>> Creating RooUnfoldResponse..."
    resp   = RooUnfoldResponse(dyhist,dyhist_gen,resphist)
    print ">>> Creating RooUnfoldBinByBin..."
    unfold = RooUnfoldBinByBin(resp,obsdyhist)
    #unfold.unfold()
    print ">>> Creating Hreco..."
    dyhist_unf = unfold.Hreco()
    sfhist = dyhist_unf.Clone(hname+"_weight")
    sfhist.Divide(dyhist_gen)
    
    # WRITE
    print ">>> Writing histograms to %s..."%(outfile.GetPath())
    outfile.cd()
    writehist(sfhist,    hname+"_weight","Z boson unfolding weight", xvar_reco.title,rtitle)
    ctrldir.cd()
    writehist(obshist,   hname+"_obs_reco",   "Observed",           xvar_reco.title,"Events")
    writehist(exphist,   hname+"_exp_reco",   "Expected",           xvar_reco.title,"Events")
    writehist(dyhist,    hname+"_dy_reco",    "Drell-Yan reco",     xvar_reco.title,"Events")
    writehist(bkghist,   hname+"_bkg_reco",   "Exp. background",    xvar_reco.title,"Events")
    writehist(obsdyhist, hname+"_obsdy_reco", "Obs. - bkg.",        xvar_reco.title,"Events")
    writehist(dyhist_gen,hname+"_dy_gen",     "Drell-Yan generator",xvar_gen.title,"Events")
    writehist(dyhist_unf,hname+"_dy_unfold",  "Drell-Yan unfolded", xvar_gen.title,"Events")
    writehist(resphist,  hname+"_dy_response","Response matrix",    xvar_gen.title,xvar_reco.title,"Events")
    
    # PLOT - weight
    print ">>> Plotting..."
    pname_ = repkey(pname,CAT="weight_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,sfhist,dividebins=False)
    plot.drawline(*line,color=kRed,title="Z boson unfolding weight")
    plot.draw(logx=logx,xmin=1.0,ymin=0.2,ymax=1.8)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions - 
    pname_ = repkey(pname,CAT="dy_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,[dyhist,obsdyhist,dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    plot.draw(ptitle,logx=logx,logy=True,xmin=1.0,title="Events / GeV",style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions - normalized
    pname_ = repkey(pname,CAT="dy_norm_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,[dyhist,obsdyhist,dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    plot.draw(ptitle,logx=logx,logy=True,xmin=1.0,norm=True,style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy_norm",gStyle.kOverwrite)
    plot.close()
    
    #### PLOT - Drell-Yan distributions - gen vs. unfolded
    ###pname_ = repkey(pname,CAT="dy_gen_"+selection.filename).replace('_baseline',"")
    ###plot   = Plot(xvar_gen,[dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    ###plot.draw(logx=logx,logy=True,xmin=1.0,title="Events / GeV")
    ###plot.drawlegend()
    ###plot.drawtext(selection.title)
    ###plot.saveas(pname_,ext=['.png','.pdf'])
    ###plot.canvas.Write("dy_gen",gStyle.kOverwrite)
    ###plot.close()
    ###
    #### PLOT - Drell-Yan distributions - gen vs. unfolded - normalized
    ###pname_ = repkey(pname,CAT="dy_gen_norm_"+selection.filename).replace('_baseline',"")
    ###plot   = Plot(xvar_gen,[dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    ###plot.draw(logx=logx,logy=True,xmin=1.0,norm=True)
    ###plot.drawlegend()
    ###plot.drawtext(selection.title)
    ###plot.saveas(pname_,ext=['.png','.pdf'])
    ###plot.canvas.Write("dy_gen_norm",gStyle.kOverwrite)
    ###plot.close()
    
    # PLOT 2D - Response matrix
    pname_ = repkey(pname,CAT="response_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_gen,xvar_reco,resphist)
    plot.draw(logx=logx,logy=logy,xmin=1.0,ztitle="Events")
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("response_matrix",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Obs. / Exp.
    pname_ = repkey(pname,CAT="data-mc_"+selection.filename).replace('_baseline',"")
    plot   = Stack(xvar_reco,obshist,hists.exp)
    plot.draw(logx=logx,logy=logy,xmin=1.0,title="Events / GeV")
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("data_mc",gStyle.kOverwrite)
    plot.close()
    
    # CLOSE
    close([exphist,bkghist,obsdyhist]) #sfhist,obshist,+hist.exp
    outfile.Close()
    print ">>> "
    


def main(args):
  channel  = 'mumu'
  eras     = args.eras
  parallel = args.parallel
  outdir   = "weights" #/$ERA"
  plotdir  = "weights/$ERA"
  fname    = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  tag      = ""
  for era in eras:
    tag_   = tag+'_'+era
    setera(era) # set era for plot style and lumi-xsec normalization
    outdir_  = ensuredir(repkey(outdir,ERA=era))
    plotdir_ = ensuredir(repkey(plotdir,ERA=era))
    samples  = getsampleset(channel,era,fname=fname,dyweight="",dy="")
    measureZpt_unfold(samples,outdir=outdir_,plotdir=plotdir_,parallel=parallel,tag=tag_)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Measure Z pT reweighting in dimuon events with RooUnfold."""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['2017'], action='store',
                                         help="set era" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print ">>> Done."
  
