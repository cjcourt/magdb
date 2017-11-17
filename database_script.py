import time
from database import MagnetismDatabase

corpus = '//home/cdt1606/Desktop/Work/Data/XML/curie/'
corpus2 = '//home/cdt1606/Desktop/Work/Data/XML/neel/'
mdb = MagnetismDatabase(corpus, 'phase_transitions', start=4920)

mdb2 = MagnetismDatabase(corpus2, 'phase_transitions', start=0)
