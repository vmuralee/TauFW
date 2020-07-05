# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
from TauFW.Plotter.sample.utils import LOG, TH1


class HistSet(object):
  """Collect samples into one set to draw histgrams from trees for data/MC comparisons,
  and allow data-driven background estimations.
  """
  
  def __init__(self, vars=[ ], data=True, exp=True, sig=False):
    self.vars   = vars
    self.data   = {v: None for v in vars} if data else { } # data histograms
    self.exp    = {v: [ ] for v in vars}  if exp  else { } # background histograms (Drell-Yan, ttbar, W+jets, ...)
    self.signal = {v: [ ] for v in vars}  if sig  else { } # signal histograms (for new physics searches)
  
  def __len__(self):
    """Start iteration over samples."""
    return len(self.vars) if hasattr(self.vars,'len') else 1
  
  def __iter__(self):
    """Start iteration over samples.
    Returns Variable, TH1D, list (of TH1D), list (of TH1D)"""
    vars = self.vars
    data = self.data
    exp  = self.exp
    sig  = self.signal
    if isinstance(vars,list):
      nvars = len(vars)
      if (exp and len(exp)!=nvars) or (sig and len(sig)!=nvars):
        LOG.warning("HistSet.__init__: Number of histograms (data=%d,exp=%d,sig=%s) does not match number of variables (%s)"%(
                    len(data),len(exp),len(sig),nvars))
      if not isinstance(data,dict) and not isinstance(exp,dict) and (not sig or isinstance(sig,dict)):
        LOG.warning("HistSet.__init__: Types do not match: data=%s, exp=%s, sig=%s"%(
                    type(data),type(exp),type(sig)))
      if self.signal:
        for var in self.vars:
          yield var, data[var], exp[var], sig[var]
      else:
        for var in self.vars:
          yield var, data[var], exp[var]
    else:
      if self.signal:
        yield vars, data, exp, sig
      else:
        yield vars, data, exp
  
  def setsingle(self):
    """Make a single result: convert result dictionaries to TH1D of list of TH1Ds
    one variable, one data hist, one exp. list and one signal list."""
    self.var    = self.vars[0]
    self.data   = self.data.get(self.var,None)
    self.exp    = self.exp.get(self.var,[ ])
    self.signal = self.signal.get(self.var,[ ])
  
  def printall(self,full=False):
    """Print for debugging purposes."""
    print ">>> HistSet: nvars=%d, ndata=%d, nexp=%d, nsig=%d"%(
                        len(self.vars),len(self.data),len(self.exp),len(self.signal))
    if full:
      print ">>>   vars=%s"%(self.vars)
      print ">>>   data=%s"%(self.data)
      print ">>>   exp=%s"%(self.exp)
      print ">>>   sig=%s"%(self.signal)
    else:
      print ">>>   vars = %s"%((', '.join(repr(str(v)) for v in self.vars) if isinstance(self.vars,list) else self.vars))
      if self.data and isinstance(self.data,dict):
        print ">>>   data = %s"%(', '.join(repr(h.GetName()) for v,h in self.data.iteritems()))
      elif isinstance(self.data,TH1):
        print ">>>   data = %r"%(self.data.GetName())
      else:
        print ">>>   data = %s"%(self.data)
      def printset(dtype,set):
        """Help function to print exp and signal histogram sets (dictionaries or lists)."""
        if isinstance(set,dict):
          for var, hlist in set.iteritems():
            print ">>>   %s['%s'] = %s"%(dtype,var,', '.join(repr(h.GetName()) for h in hlist))
        elif isinstance(set,list) and set:
          print ">>>   %-4s = %s"%(dtype,', '.join(repr(h.GetName()) for h in set))
        else:
          print ">>>   %-4s = %s"%(dtype,set)
      printset('exp',self.exp)
      printset('sig',self.signal)
  


