import os
import sys

curDir = os.getcwd()
shared_dir = '/home/oreheem/shared'
openroadDir = "/OpenROAD/build/src/"
seed_fr = 0
numSeeds_tr = 1
gen = 1
patch_seeds = "0_0"
base = 13
hotspot_th = 8
fidx = "0100"
# run openroad with fastroute
# generate .guide to ./fr_results/ 

# sort .guide file to _sorted.guide
def Sort(sub_li):
  sub_li.sort(key = lambda x: x[0])
  return sub_li

if gen == 0:
  f = open(str(shared_dir)+'/fr_seed.tcl.temple','r')
  lines = f.readlines()
  f.close()

  fo = open(str(shared_dir)+'/fr_params/run_single_fr_seed_%s.tcl'%(seed_fr),'w')
  for line in lines:
      if line.startswith("set seed"):
          line = "set seed {}\n".format(seed_fr)
      fo.write(line)
  fo.close()
  cmd = '%s/openroad %s/fr_params/run_single_fr_seed_%s.tcl |tee %s/log/log_fr_out_seed_%s.log'%(openroadDir,shared_dir,seed_fr,shared_dir,seed_fr)
  print(cmd)
  os.system(cmd)

if gen == 0:
  f = open(str(shared_dir)+'/fr_results/out_seed_%s.guide'%(seed_fr), 'r')
else:
  f = open(str(shared_dir)+'/fr_results/F_gen_%s_b_%s_p_%s_th_%s_%s.guide'%(gen, base, patch_seeds, hotspot_th, fidx), 'r')
lines = f.readlines()
f.close()

net = []
netlist = []
flagName = 1
for line in lines:
  if flagName == 1:
    netName = line
    #print(netName)
    net.append(netName)
    flagName = 0
    continue
  if flagName == 0:
    net.append(line)
    if line == ")\n":
      flagName = 1
      netlist.append(net)
      net = []
Sort(netlist)
#print(netlist)


if gen == 0:
  guidesFName = "%s/fr_results/out_seed_%s_sorted.guide"%(shared_dir,seed_fr)
else:
  guidesFName = str(shared_dir)+'/fr_results/F_gen_%s_b_%s_p_%s_th_%s_%s_sorted.guide'%(gen, base, patch_seeds, hotspot_th, fidx)
fo = open(guidesFName, 'w')
for nets in netlist:
  for line in nets:
    fo.write(line)
fo.close()


# run TritonRoute14

for seed_tr in range(0,numSeeds_tr):
    trDir = str(shared_dir)
    f = open(str(shared_dir)+'/tr_seed.tcl.temple','r')
    lines = f.readlines()
    f.close()
    if gen == 0:
      foName = '%s/tr_params/run_out_fr_%s_tr_%s_sorted.tcl'%(shared_dir,seed_fr,seed_tr)
    else:
      foName = '%s/tr_params/run_out_gen_%s_p_%s_sorted.tcl'%(shared_dir,gen,fidx)
    fo = open(foName, 'w')
    for line in lines:
      if gen == 0:
        if line.startswith("set frseed"):
          line = "set frseed {}\n".format(seed_fr)
        if line.startswith("set trseed"):
          line = "set trseed {}\n".format(seed_tr)
      else:
        if line.startswith("set output_drc"):
          line = "set output_drc \"{}/tr_results/out_gen_{}_p_{}_sorted.outputDRC.rpt\"\n".format(shared_dir, gen, fidx)
        if line.startswith("set input_guides"):
          line = "set input_guides \"{}\"\n".format(guidesFName)
        if line.startswith("set output_def"):
          line = "set output_def \"{}/tr_results/out_gen_{}_p_{}_sorted_routed.def\"\n".format(shared_dir, gen, fidx)
        
      fo.write(line)
    fo.close()
    if gen == 0:
      logName = "%s/log/log_out_fr_%s_tr_%s_sorted.log"%(shared_dir, seed_fr, seed_tr)
    else:
      logName = "%s/log/log_out_gen_%s_p_%s_sorted.log"%(shared_dir, gen, fidx)
    cmd = "%s/openroad %s |tee %s"%(openroadDir,foName, logName)
    print(cmd)
    os.system(cmd)
