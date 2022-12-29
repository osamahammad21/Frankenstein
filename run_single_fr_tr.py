import os
import sys

curDir = os.getcwd()
#curDir = '/home/sek006/scratch/03_HybridVigor/runs/ispd18_test4'

seed_fr = 0
numSeeds_tr = 1
# run openroad with fastroute
# generate .guide to ./fr_results/ 
f = open(str(curDir)+'/fr_seed.tcl.temple','r')
lines = f.readlines()
f.close()

fo = open(str(curDir)+'/fr_params/run_single_fr_seed_%s.tcl'%(seed_fr),'w')
for line in lines:
    if line.startswith("set seed"):
        line = "set seed {}\n".format(seed_fr)
    fo.write(line)
fo.close()




openroadDir = "/home/osama/Desktop/OpenROAD-new/build/src"
cmd = '%s/openroad %s/fr_params/run_single_fr_seed_%s.tcl |tee %s/log/log_fr_out_seed_%s.log'%(openroadDir,curDir,seed_fr,curDir,seed_fr)
print(cmd)
os.system(cmd)
# sort .guide file to _sorted.guide
def Sort(sub_li):
  sub_li.sort(key = lambda x: x[0])
  return sub_li

f = open(str(curDir)+'/fr_results/out_seed_%s.guide'%(seed_fr), 'r')
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


fo = open("%s/fr_results/out_seed_%s_sorted.guide"%(curDir,seed_fr), 'w')
for nets in netlist:
  for line in nets:
    fo.write(line)
fo.close()


# run TritonRoute14

for seed_tr in range(0,numSeeds_tr):
    trDir = str(curDir)
    f = open(str(curDir)+'/tr_seed.tcl.temple','r')
    lines = f.readlines()
    f.close()

    fo = open('%s/tr_params/run_out_fr_%s_tr_%s_sorted.tcl'%(curDir,seed_fr,seed_tr),'w')
    for line in lines:
      if line.startswith("set frseed"):
        line = "set frseed {}\n".format(seed_fr)
        
      if line.startswith("set trseed"):
        line = "set trseed {}\n".format(seed_tr)
        
      fo.write(line)
    fo.close()
    cmd = "%s/openroad %s/tr_params/run_out_fr_%s_tr_%s_sorted.tcl |tee %s/log/log_out_fr_%s_tr_%s_sorted.log"%(openroadDir,curDir,seed_fr,seed_tr,curDir,seed_fr,seed_tr)
    print(cmd)
    os.system(cmd)



