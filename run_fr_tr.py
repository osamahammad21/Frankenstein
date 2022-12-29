import os
import sys
from k8swrapper import K8SExecutor
import time
numSeeds_fr = 50
numSeeds_tr = 1
curDir = os.getcwd()
executor = K8SExecutor()
f = open(str(curDir)+'/run_single_fr_tr.py','r')
lines = f.readlines()
f.close()
shared_dir = '/home/oreheem/shared'
jobs = {}
remaining = 0
for seed_fr in range(0,numSeeds_fr):
    fo = open(str(shared_dir)+'/runs/run_fr_tr_%s_%s.py'%(seed_fr,numSeeds_tr),'w')
    for line in lines:
        if line.startswith('seed_fr'):
            line = "seed_fr = %s\n"%(seed_fr)
        if line.startswith('numSeeds_tr'):
            line = "numSeeds_tr = %s\n"%(numSeeds_tr)
        fo.write(line)
    fo.close()
    jobId = executor.runJob('%s/runs/run_fr_tr_%s_%s.py'%(shared_dir,seed_fr,numSeeds_tr))
    jobs[seed_fr] = {"job_id":jobId,'done':False}
    remaining += 1

while remaining > 0:
    time.sleep(60)
    for seed in jobs:
        if jobs[seed]['done']:
            continue
        status = executor.getJobStatus(jobs[seed]['job_id'])
        if status.succeeded:
            remaining -= 1
            jobs[seed]['done'] = True
            print('seed {} returned'.format(seed))

