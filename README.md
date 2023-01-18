
Refer to the paper "Frankenstein Global Routes Have Hybrid Vigor" for the theoritical explanation.

# Prerequisites
* First, you need to setup an nfs server that is gonna be used by the kubernetes cluster for reading inputs and writing outputs. Refer to https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nfs-mount-on-ubuntu-20-04 for setting up the server and the client machine. Make sure that the nfs volume is mounted at the same path for the server, client and the k8s containers.
* You need to create a k8s cluster with the needed resources (cpus and memory).
* From the client machine (the one you will be using for managing the whole flow), authenticate to the k8s cluster.
* change the variable "shared_dir" to the path the nfs volume is mounted to. You should change the variable in Frankenstein.py, run_fr_tr.py and run_single_fr_tr.py
* Copy fr_seed.tcl.temple and tr_seed.tcl.temple to the shared directory.
* Download the ispd design in the shared directory. It should be as following {path_to_shared_dir}/ispd19_test2/
* Change the "design" variable in Frankenstein.py to the downloaded design name.
* Change the lef/def/guides path in fr_seed.tcl.temple and tr_seed.tcl.temple to the corresponding paths.
# Frankenstein flow
* run "python3 run_fr_tr.py --gen 0" on the client machine
* After all the results have returned, run "python3 Frankenstein.py --gen 1 --base_rank 0 --hotspot_th 8". You could change the hotspot threshold and base rank as you wish.
* run "python3 run_fr_tr.py --gen 1" on the client machine to run the next generation. follow the same pattern for further generations.
# Explanation
* run_fr_tr.py, is responsible for creating k8s jobs for the current generation of routes.
* Frankenstein.py loads the generation results, identify DRC hotspots, patch the guides for the upcoming Frankenstein generation.
* You can also use run report_runs.py to generate a csv file that has the number of violations for each seed or frankenstein path guide.
