import os
import sys


numSeeds_fr = 5
numSeeds_tr = 3
curDir = os.getcwd()
# curDir = '/home/sek006/scratch/03_HybridVigor/runs/ispd18_test4'

f = open(str(curDir)+'/run_single_fr_tr.py','r')
lines = f.readlines()
f.close()

for seed_fr in range(0,numSeeds_fr):
    fo = open(str(curDir)+'/runs/run_fr_tr_%s_%s.py'%(seed_fr,numSeeds_tr),'w')
    for line in lines:
        if line.startswith('seed_fr'):
            line = "seed_fr = %s\n"%(seed_fr)
        if line.startswith('numSeeds_tr'):
            line = "numSeeds_tr = %s\n"%(numSeeds_tr)
        fo.write(line)
    fo.close()
    cmd = 'python3 %s/runs/run_fr_tr_%s_%s.py'%(curDir,seed_fr,numSeeds_tr)
    print(cmd)

