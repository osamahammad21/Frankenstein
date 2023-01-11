import sys
import os
import time
from multiprocessing import Pool
import signal
import numpy as np
import itertools
from itertools import combinations
import pprint
import decimal
from rtree import index
from rtree.index import Rtree
import argparse
import re
import shutil


CLI=argparse.ArgumentParser()
CLI.add_argument(
        "--patches",
        nargs="*",
        type=int,
)
CLI.add_argument(
        "--gen",
        nargs="*",
        type=int,
)
CLI.add_argument(
        "--base_rank",
        nargs="*",
        type=int,
)
CLI.add_argument(
        "--base",
        nargs="*",
        type=int,
)
CLI.add_argument(
        "--hotspot_th",
        nargs="*",
        type=int,
)
args = CLI.parse_args()

design='ispd19_test9'
numSeeds_fr = 50
winSteps = [100]
max_hotspot_num = 3 #will depress to 2
skipSeeds = [43, 20]  # this is already too good solution.
hotspot_th = int(args.hotspot_th[0])
base_rank = int(args.base_rank[0])  # 0 1 2 3 4. 
gen = int(args.gen[0])
shared_dir = "/home/oreheem/shared"


if gen ==1:
    f_gen = open(shared_dir+'/genealogy_%s_th_%s_baseRnk_%s.log'%(design,hotspot_th,base_rank),'w')
else:
    f_gen = open(shared_dir+'/genealogy_%s_th_%s_baseRnk_%s.log'%(design,hotspot_th,base_rank),'a')

idx = index.Index()


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def init_setting():
    dbu =0
    f = open(shared_dir+'/tr_results/out_fr_0_tr_0_sorted_routed.def','r')
    while True:
        line = f.readline()
        if not line: break
        if line.startswith('UNITS'):
            dbu = int(line.split()[3])
        if line.startswith('DIEAREA'):
            dMinX = int(line.split()[2])
            dMinY = int(line.split()[3])
            dMaxX = int(line.split()[6])
            dMaxY = int(line.split()[7])
            break
    f.close()
    dHalfX = int(dMaxX/2)
    dHalfY = int(dMaxY/2)

    findDir = shared_dir+"/fr_results"
    dirList = os.listdir(findDir)
    return dbu,dHalfX,dHalfY,dMinX,dMinY,dMaxX,dMaxY


def intersects(bb1, bb2):
    return not (bb1[2] < bb2[0] \
    or bb1[0] > bb2[2] \
    or bb1[3] < bb2[1] \
    or bb1[1] > bb2[3])

def remove_dupl_dict(test_list):
    res_list = [i for n, i in enumerate(test_list) if i not in test_list[n + 1:]] 
    return(res_list)

def merge_DRC(fr_seed):
    findDir=shared_dir+"/tr_results/"
    dirList=os.listdir(findDir) 

    DRC = []
    for dName in sorted(dirList):
        if (dName.startswith('%s_out_fr_%s_'%(design,fr_seed))==False):
            continue
        f=open(shared_dir+'/tr_results/%s'%(dName), 'r')
        drc_lines = f.readlines()
        f.close()
        flagDRC=1
        for line in drc_lines:
            if flagDRC==1:
                if line.split()[0]=='violation':
                    typeDRC = line.split()[2]
                flagDRC=0
                bb=[]
                continue
            if flagDRC==0:
                if line.split()[0]=='srcs:':
                    netDRC=[]
                    for i in range(1,len(line.split())):
                        t_src = line.split()[i].strip('\n').replace('\\','')
                        netDRC.append(t_src)
                    
                    continue
                if line.split()[0]=='bbox':
                    bMinX=int(float(line.split()[3].strip(','))*dbu)
                    bMinY=int(float(line.split()[4])*dbu)
                    bMaxX=int(float(line.split()[8].strip(','))*dbu)
                    bMaxY=int(float(line.split()[9])*dbu)
                    bLayer=line.split()[13]
                    bb = [bMinX, bMinY, bMaxX, bMaxY]
                    flagDRC=1
                    DRC.append(dict({'type':typeDRC, 'srcs':netDRC, \
                            'bbox': bb}))
    return (DRC)

def merge_F_DRC(fName):

    DRC = []
    f=open(fName, 'r')
    drc_lines = f.readlines()
    f.close()
    DRC_list = []
    flagDRC=1
    for line in drc_lines:
        if flagDRC==1:
            if line.split()[0]=='violation':
                typeDRC = line.split()[2]
            flagDRC=0
            bb=[]
            continue
        if flagDRC==0:
            if line.split()[0]=='srcs:':
                netDRC=[]
                for i in range(1,len(line.split())):
                    t_src = line.split()[i].strip('\n').replace('\\','')
                    netDRC.append(t_src)
                
                continue
            if line.split()[0]=='bbox':
                bMinX=int(float(line.split()[3].strip(','))*dbu)
                bMinY=int(float(line.split()[4])*dbu)
                bMaxX=int(float(line.split()[8].strip(','))*dbu)
                bMaxY=int(float(line.split()[9])*dbu)
                bLayer=line.split()[13]
                bb = [bMinX, bMinY, bMaxX, bMaxY]
                flagDRC=1
                DRC.append(dict({'type':typeDRC, 'srcs':netDRC, \
                        'bbox': bb}))
    DRC_merged = DRC
    return (DRC_merged)

def find_best_hotspot(DRC_list,seed_fr):
    id=int(seed_fr)
    max_bb = []
    n_hotspot_bb = []

    print("#DRVs:",len(DRC_list))
    print(dMaxX, dMaxY)
    total_density = len(DRC_list)/int(((dMaxX - dMinX)*(dMaxY - dMinY)))
    print(total_density)
    
    comb = list(combinations(DRC_list,2))
    for i in range(0,len(comb)):
        xMin = int(min(comb[i][0]['bbox'][0],comb[i][1]['bbox'][0]))
        yMin = int(min(comb[i][0]['bbox'][1],comb[i][1]['bbox'][1]))
        xMax = int(max(comb[i][0]['bbox'][2],comb[i][1]['bbox'][2]))
        yMax = int(max(comb[i][0]['bbox'][3],comb[i][1]['bbox'][3]))
        print(id,(xMin, yMin, xMax, yMax),i)
        idx.insert(id,(xMin, yMin, xMax, yMax),i)

        cnt = 0
        for j in range(0,len(DRC_list)):
            hits = list(idx.intersection((DRC_list[j]['bbox']),objects=False))
            if len(hits)>0:
                cnt= cnt+1
        idx.delete(id,(xMin, yMin, xMax, yMax))
        x_size = xMax-xMin
        y_size = yMax-yMin
        cnt = cnt

        if x_size==0:
            x_size=1
        if y_size==0:
            y_size=1
        t= cnt/(x_size*y_size)
        if cnt>int((len(DRC_list)/hotspot_th)):
            temp_bb = [xMin, yMin, xMax, yMax]
            bb_pair = [t, cnt, temp_bb]
            max_bb.append(bb_pair)
    max_bb.sort(key = lambda x: x[0],reverse=True)

    #i[0]: density, [1]: #DRVs in the hotspot, [2]: hotspot bb
    for i in range(0,len(max_bb)):
        if i==0:
            n_hotspot_bb.append(max_bb[i])
        else:
            for t in range(0,i):
                isTouch = intersects(max_bb[i][2],max_bb[t][2])
                if isTouch==1:
                    break
            if isTouch:
                continue
            else:
                n_hotspot_bb.append(max_bb[i])

        if len(n_hotspot_bb)==max_hotspot_num:
            break
    return(n_hotspot_bb)

def find_Frankenstein_nets(bb1,fr):
    F_netlist = []
    net=[]
    findDir=shared_dir+"/fr_results/"
    dirList=os.listdir(findDir) 
    for dName in sorted(dirList):
        if gen==1:
            if dName.startswith('out_seed_%s_sorted'%(fr))==False:
                continue
        else:
            if dName.startswith('F_gen_%s'%(gen-1))==False:
                continue
            if dName.endswith('_%s.guide'%(fr))==False:
                continue
        f=open(shared_dir+'/fr_results/%s'%(dName), 'r')
        lines = f.readlines()
        f.close()
        flagTouch=0
        flagName = 1
        for line in lines:
            if flagName == 1:
                netName = line
                net.append(netName)
                flagName = 0
                continue
            elif flagName == 0:
                if line ==")\n":
                    flagName=1
                    flagTouch=0
                else:
                    if line!="(\n":
                        if flagTouch==1:
                            continue
                        minX = int(line.split()[0])
                        minY = int(line.split()[1])
                        maxX = int(line.split()[2])
                        maxY = int(line.split()[3])
                        bb2 = [minX, minY, maxX, maxY]
                        isTouch = intersects(bb1,bb2)
                        if isTouch :
                            F_netlist.append(netName)
                            flagTouch=1
                            continue
    return F_netlist,net

def Franken_combine(patches, base, idx_cnt):
    patch_seeds = ""
    t_idx = ""
    for i in patches:
        patch_seeds = patch_seeds+"_"+str(i[0])
        t_idx = "%s%s"%(t_idx,i[0])
    f_idx='%02d%02d'%(gen,idx_cnt)
    dName_F = 'F_gen_%s_b_%s_p%s_th_%s_%s.guide'%(gen,base,patch_seeds,hotspot_th,f_idx)
    fo=open('./tmp/%s'%(dName_F), 'w')
    for patch_num in range(0,len(patches)):
        F_seed = patches[patch_num][0]
        F_nets = patches[patch_num][1]
        if gen==0:
            # it is from orignal GR sols
            dName_patch = 'out_seed_%s_sorted.guide'%(F_seed)
        else:
            # it is from Frankenstein GR sols
            findDir=shared_dir+'/fr_results/'
            dirList=os.listdir(findDir)
            for dName in sorted(dirList):
                if dName.endswith('_%s.guide'%(F_seed)):
                    dName_patch = dName
        if not os.path.exists('./tmp/%s'%(dName_patch)):
            shutil.copy(shared_dir+'/fr_results/%s'%(dName_patch), './tmp/%s'%(dName_patch))
        f_patch=open('./tmp/%s'%(dName_patch), 'r')
        lines = f_patch.readlines()
        f_patch.close()
        flagName = 1
        flagWrite = 0
        writtenNets = set([])
        buffer = ''
        F_nets_set = set(F_nets)
        for line in lines:
            if flagName == 1:
                netName = line
                flagName = 0
                if netName in F_nets_set:
                    writtenNets.add(netName)
                    flagWrite = 1
                    # fo.write(line)
                    buffer += line
            elif flagName == 0:
                if flagWrite == 1:
                    # fo.write(line)
                    buffer += line
                    if line ==")\n":
                        flagName=1
                        flagWrite = 0
                else:
                    if line==")\n":
                        flagName=1
                        flagWrite = 0
            if len(buffer) == 1e6:
                fo.write(buffer)
                buffer = ''
        if len(buffer) != 0:
            fo.write(buffer)
        print("Added seed",F_seed)
    if gen == 1:
        # it is from orignal GR sols
        dName_base = 'out_seed_%s_sorted.guide'%(base)
    else:
        # it is from Frankenstein GR sols
        findDir=shared_dir+'/fr_results/'
        dirList=os.listdir(findDir)
        
        for dName in sorted(dirList):
            if dName.endswith('_%s.guide'%(base)):
                dName_base = dName
    if not os.path.exists('./tmp/%s'%(dName_base)):
        shutil.copy(shared_dir+'/fr_results/%s'%(dName_base), './tmp/%s'%(dName_base))
    f_base=open('./tmp/%s'%(dName_base), 'r')
    lines = f_base.readlines()
    f_base.close()
    
    
    flagName=1
    flagWrite=0
    buffer = ''
    for line in lines:
        if flagName==1:
            netName = line
            flagName = 0
            if netName in writtenNets:
                continue
            else:
                buffer += line
                # fo.write(line)
                flagWrite =1
        else:
            if flagWrite==1:
                buffer += line
                # fo.write(line)
                if line==")\n":
                    flagName=1
                    flagWrite=0
            else:
                if line==")\n":
                    flagName=1
        if len(buffer) == 1e6:
            fo.write(buffer)
            buffer = ''
    if len(buffer) != 0:
        fo.write(buffer)

    fo.close()

def call_net_guide(net, fr_seed):
    if int(fr_seed)<80:
        dName = 'out_seed_%s_sorted.guide'%(fr_seed)
    else:
        findDir=shared_dir+'/fr_results/'
        dirList=os.listdir(findDir)
        for tdName in sorted(dirList):
            if tdName.endswith('_%s.guide'%(fr_seed)):
                dName = tdName
    f = open(shared_dir+'/fr_results/%s'%dName,'r')
    lines = f.readlines()
    f.close()
    flagName = 1
    flagFind = 0
    return_net_guide = []
    for line in lines:
        if flagName==1:
            netName = line
            flagName=0
            
            if netName==net:
                flagFind=1
        else:
            if flagFind==1:
                if line!= "(\n" and line!=")\n":
                    return_net_guide.append(line)
                if line==")\n":
                    return sorted(return_net_guide)
            else:
                if line==")\n":
                    flagName=1

def compare_set(temp_pairs):
    idx_delete = []
    for i in range(1,len(temp_pairs)):
        fr_seed = temp_pairs[i][0]
        netlists = temp_pairs[i][1]
        DRCs = temp_pairs[i][2]
        prev_fr_seed = temp_pairs[i-1][0]
        prev_DRCs = temp_pairs[i-1][2]
        flagDiff=0
        for net in netlists:
            t1_list = call_net_guide(net,prev_fr_seed)
            t2_list = call_net_guide(net,fr_seed)
            if t1_list!=t2_list:
                print(t1_list)
                print(t2_list)
                flagDiff=1
        print("FLAG:",flagDiff)



###

# read DBU and die size from final DEF file
dbu,dHalfX,dHalfY,dMinX,dMinY,dMaxX,dMaxY=init_setting()
# find best GR seed solution, --> pick M (base_rank) << N parents (original GR sols). 
if gen==1:
    base_drc_num = 1000000
    DRC_list = []
    for i in range(0,numSeeds_fr):
        if any(i== t for t in skipSeeds ): continue
        merge_DRC_pair = [i, merge_DRC(i)]
        # print(i, merge_DRC(i))
        DRC_list.append(merge_DRC_pair)
    DRC_list.sort(key = lambda x: len(x[1]))
    
    base = DRC_list[base_rank][0]
    base_drc_num = len(DRC_list[base_rank][1])
    base_drc = DRC_list[base_rank][1]
else:
    base_drc_num = 1000000
    DRC_list = []
    findDir=shared_dir+'/tr_results/'
    dirList=os.listdir(findDir)
    for dName in sorted(dirList):
        if dName.startswith('out_gen_%s_'%(gen-1))==False:
            continue
        if  ".def" in dName:
            continue
        results = re.findall('[0-9]+', dName)
        merge_DRC_pair = [results[1], merge_F_DRC(findDir+dName)]
        DRC_list.append(merge_DRC_pair)
    DRC_list.sort(key = lambda x: len(x[1]))

    base = str(DRC_list[base_rank][0])
    base_name = DRC_list[base_rank][0]
    base_drc_num = len(DRC_list[base_rank][1])
    base_drc = DRC_list[base_rank][1]
        
print("GEN %s - base seed: %s #DRVs: %s"%(gen, base, base_drc_num))
f_gen.write("GEN %s - base seed: %s #DRVs: %s \n"%(gen, base, base_drc_num))
for i in base_drc:
    log_bb = "%s %s %s %s \n"%(i['bbox'][0], i['bbox'][1], i['bbox'][2], i['bbox'][3])
    f_gen.write(log_bb)

n_hotspot_bb = find_best_hotspot(base_drc,base)

#i[0]: density, [1]: #DRVs in the hotspot, [2]: hotspot bb
for i in range(0,len(n_hotspot_bb)):
    f_gen.write("GEN %s - hotspot %s bb: %s %s %s %s #DRVs: %s \n"\
    %(gen, i, n_hotspot_bb[i][2][0], n_hotspot_bb[i][2][1], \
    n_hotspot_bb[i][2][2], n_hotspot_bb[i][2][3], n_hotspot_bb[i][1]))
    print("GEN %s - hotspot %s bb: %s %s %s %s #DRVs: %s"\
    %(gen, i, n_hotspot_bb[i][2][0], n_hotspot_bb[i][2][1], \
    n_hotspot_bb[i][2][2], n_hotspot_bb[i][2][3], n_hotspot_bb[i][1]))

#Create a netlist belonging to the Frankenstein region from best fr seed

F_netlist_list = []
net_list=[]
 
#i[0]: density, [1]: #DRVs in the hotspot, [2]: hotspot bb

patches_list = []
h_num = 0
print(n_hotspot_bb)
for hotspot_i in n_hotspot_bb:
    
    F_netlist,net = find_Frankenstein_nets(hotspot_i[2],base)
    #F_netlist_list.append(F_netlist)
    #net_list.append(net)
    F_netlist = list(set(F_netlist))

    F_min_drc = 100000
    temp_pairs = []
    if gen == 1:
        ### methodd : patch search -- original GR sols part
        for i in range(0,numSeeds_fr):
            if i in skipSeeds:
                continue
            if i==base:
                continue
            cnt = 0
            skil_flag=0
            for d in merge_DRC(i):
                bb_d  = [int(d['bbox'][0]), \
                        int(d['bbox'][1]), \
                        int(d['bbox'][2]), \
                        int(d['bbox'][3])]
                if intersects(bb_d, hotspot_i[2]):
                    cnt = cnt + 1
            temp_pairs.append([i, F_netlist, cnt])
    else:

    ### methodd : patch search -- F GR sols part
        findDir=shared_dir+'/tr_results/'
        dirList=os.listdir(findDir)
        for dName in sorted(dirList):
            if dName.startswith('out_gen_%s_'%(gen-1))==False:
                continue
            if  ".def" in dName:
                continue
            results = re.findall('[0-9]+', dName)
            cnt=0
            for d in merge_F_DRC(findDir+dName):
                bb_d  = [int(d['bbox'][0]), \
                        int(d['bbox'][1]), \
                        int(d['bbox'][2]), \
                        int(d['bbox'][3])]
                if intersects(bb_d, hotspot_i[2]):
                    cnt = cnt + 1
            temp_pairs.append([results[1], F_netlist, cnt])
    ######################

    temp_pairs.sort(key = lambda x: x[2],reverse=False)
    if len(temp_pairs)>5:
        del temp_pairs[5:len(temp_pairs)]
        #print(temp_pairs)
    patches_list.append(temp_pairs)
    h_num = h_num+1

# 핫스팟을 넣어주고, 각 핫스팟에 대하여 5위 DRC갯수 까지 시드, netlist, DRC갯수 리턴

#print("patches:",patches_list)
# If one net spans two or more hotspots, choose one of the following:
# method 1: ignore that net.
# method 2: delete from better hotspot (remain worse hotspot)
# method 3: delete from worse hotspot (remain better hotspot)
# method 4: if two hotspots have same nets, ignore better hotspot.
# method 1,2,3

guides = []
cnt=0
for x in patches_list[0]:
    if len(patches_list)>1:
        for y in patches_list[1]:
            if len(patches_list)>2:
                for z in patches_list[2]:
                    guides.append([x,y,z])
                    cnt=cnt+1
            else:
                guides.append([x,y])
                cnt=cnt+1

#guides --> [[x,y], ...]--> [[[seed1,nets1,cnt1], [seed2, nets2,cnt2]],...]
idx_cnt = 0
prev_patch_seeds = []
method4_prev_patch_seeds = []
for patches in guides:
    #patches --> [[seed1,nets1,cnt1], [seed2, nets2,cnt2]]
    method4_del_list = []
    for i in range(1,len(patches)):
        del_list = []
        for ele in patches[i][1]: #for each net
            for j in range(0,i):
                if ele in patches[j][1]:
                    t_pair = [j,ele]
                    del_list.append(t_pair)
                    method4_del_list.append(i)

        #print(del_list)
        for del_ele in del_list:
            #print(del_ele)
            # method 1
            #patches[int(del_ele[0])][1].remove(del_ele[1])
            #patches[i][1].remove(del_ele[1])
            # method 2
            patches[i][1].remove(del_ele[1])
            # method 3
            #patches[int(del_ele[0])][1].remove(del_ele[1])

    #method 4
    #method4_del_list = list(set(method4_del_list))
    #method4_del_list.sort(reverse=True)
    #for i in method4_del_list:
    #    del patches[i]
    #    print("GEN %s - hotspot %s is deleted (now %s becomes %s)"%(gen, i, i+1,i))
    #    f_gen.write("GEN %s - hotspot %s is deleted "%(gen, i))
    #if len(patches)>2:
    #    for i in range(2,len(patches)):
    #        del patches[i]
    #patch_seeds = ""
    #for i in patches:
    #    patch_seeds = patch_seeds +" "+str(i[0])
    #if patch_seeds in method4_prev_patch_seeds:
    #    continue
    #method4_prev_patch_seeds.append(patch_seeds)
     ######################################   
    if len(patches)>2:
        for i in range(2,len(patches)):
            del patches[i]
    patch_seeds = ""
    for i in patches:
        patch_seeds = patch_seeds +" "+str(i[0])
    if patch_seeds==prev_patch_seeds:
        continue
    prev_patch_seeds=patch_seeds
    

    for h_num in range(0,len(patches)):
        print("GEN %s - hotspot %s patch seed: %s "%(gen, h_num, patches[h_num][0]))
        print("GEN %s - hotspot %s expected hotspot #DRVs: %s "%(gen, h_num, patches[h_num][2]))
        print("GEN %s - hotspot %s #nets: %s "%(gen, h_num, len(patches[h_num][1])))
        f_gen.write("GEN %s - hotspot %s patch seed: %s \n"%(gen, h_num, patches[h_num][0]))
        f_gen.write("GEN %s - hotspot %s expected hotspot #DRVs: %s \n"%(gen, h_num, patches[h_num][2]))
        f_gen.write("GEN %s - hotspot %s #nets: %s \n"%(gen, h_num, len(patches[h_num][1])))

    f_idx='%02d%02d'%(gen,idx_cnt)
    f_gen.write("GEN %s - f_idx %s patch seeds: %s \n"%(gen,f_idx, patch_seeds ))
    print("GEN %s - f_idx %s patch seeds: %s \n"%(gen,f_idx, patch_seeds ))
    

    #print("patches:",patches)

    ## combine base and F_fr to make Frankenstein Guide
    Franken_combine(patches, base, idx_cnt)
    idx_cnt = idx_cnt + 1

f_gen.close()
