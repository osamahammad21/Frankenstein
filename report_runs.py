
import sys
import re
import os



dirList=os.listdir(sys.argv[1]) 
gen = sys.argv[3]
csv = open(sys.argv[2], "w")
csv.write("seed, violations\n")
for dName in sorted(dirList):
    if gen == 0 and dName.startswith("log_out_fr") == False:
        continue
    if gen != 0 and dName.startswith("log_out_gen_%s"%(gen)) == False:
        continue
    results = re.findall('[0-9]+', dName)
    if gen == 0:
        seed = results[0]
    else:
        seed = results[1]

    log = open("%s/%s"%(sys.argv[1], dName), "r")
    lines = log.readlines()
    drvs = -1
    for line in lines:
        if line.startswith("[INFO DRT-0199]"):
            results = re.findall('[0-9]+', line)
            drvs = results[1]
    csv.write("{},{}\n".format(seed, drvs))