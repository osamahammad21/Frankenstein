import os
import sys
from k8swrapper import K8SExecutor
import time
import re
import argparse

CLI=argparse.ArgumentParser()
CLI.add_argument(
        "--gen",
        nargs="*",
        type=int,
)
args = CLI.parse_args()

gen = int(args.gen[0])
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
if gen == 0:
    for seed_fr in range(0,numSeeds_fr):
        fo = open(str(shared_dir)+'/runs/run_fr_tr_%s_%s.py'%(seed_fr,numSeeds_tr),'w')
        for line in lines:
            if line.startswith("gen = "):
                line = "gen = %s\n"%(gen)
            if line.startswith('seed_fr'):
                line = "seed_fr = %s\n"%(seed_fr)
            if line.startswith('numSeeds_tr'):
                line = "numSeeds_tr = %s\n"%(numSeeds_tr)
            fo.write(line)
        fo.close()
        jobId = executor.runJob('%s/runs/run_fr_tr_%s_%s.py'%(shared_dir,seed_fr,numSeeds_tr))
        jobs[seed_fr] = {"job_id":jobId,'done':False}
        remaining += 1
else:
    for fName in os.listdir("%s/fr_results/"%(shared_dir)):
        if not fName.startswith("F_gen_%s"%(gen)):
            continue

        results = re.findall('[0-9]+', fName)
        if len(results) < 6:
            continue
        gen = results[0]
        base = results[1]
        patch_seeds = "%s_%s"%(results[2], results[3])
        hotspot_th = results[4]
        f_idx = results[5]
        fo = open(str(shared_dir)+'/runs/run_gen_%s_p_%s.py'%(gen,patch_seeds),'w')
        for line in lines:
            if line.startswith("gen = "):
                line = "gen = %s\n"%(gen)
            if line.startswith("patch_seeds = "):
                line = "patch_seeds = \"%s\"\n"%(patch_seeds)
            if line.startswith("base = "):
                line = "base = \"%s\"\n"%(base)
            if line.startswith("hotspot_th = "):
                line = "hotspot_th = %s\n"%(hotspot_th)
            if line.startswith("fidx = "):
                line = "fidx = \"%s\"\n"%(f_idx)
            fo.write(line)
        fo.close()
        jobId = executor.runJob('%s/runs/run_gen_%s_p_%s.py'%(shared_dir,gen,patch_seeds))
        jobs[patch_seeds] = {"job_id":jobId,'done':False}
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

