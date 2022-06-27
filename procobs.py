from sigpyproc.readers import FilReader
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

SAVEDIR = "gen_imgs/"

FILE = sys.argv[1].replace("\\", "")

fil = FilReader(FILE)
block = fil.read_block(0, fil.header.nsamples_files[0])

spec = block.mean(axis = 1)[:-1]
ts = block.mean(axis = 0)[1:]

spec_db = 10 * np.log10(spec)
ts_db = 10 * np.log10(ts)

plt.plot(spec)
plt.savefig(SAVEDIR + "spec.png")
plt.clf()

plt.plot(ts)
plt.savefig(SAVEDIR + "ts.png")
plt.clf()

plt.plot(spec_db)
plt.savefig(SAVEDIR + "spec_db.png")
plt.clf()

plt.plot(ts_db)
plt.savefig(SAVEDIR + "ts_db.png")
plt.clf()
