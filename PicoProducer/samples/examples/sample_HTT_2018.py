from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/user/${USER::1}/$USER/samples/nano/$ERA/$DAS"
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None #"samples/files/2018/$SAMPLE.txt"
samples  = [
    # ggHiggsToTauTau
    M('ggH','GluGluHToTauTau_M125',"/GluGluHToTauTau_M-125_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",store=storage,url=url,files=filelist,
  )
]
