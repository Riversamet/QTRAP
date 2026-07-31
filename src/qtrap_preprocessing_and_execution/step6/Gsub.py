# NOTE:
# This script is a pre-existing Gaussian submission utility commonly
# used within UCLA computational chemistry groups and is included for
# workflow completeness. It was not written by the repository author.
#
# The script contains Hoffman2-specific module paths and queue settings
# and may require modification for use on other HPC systems.

#!/usr/bin/python
# works with 2.6.6 (default on hoffman2) and python 2.7.X
#  *** Usage of python 2.7.x is recommended ***
#   This is done via the command: module load python/2.7
#   You should add the above command to your .bashrc,
#     which will change your default python to version 2.7.15
#  The script may not fully work with python3 currently but that is a future goal
#   If anyone can help make this compatible with python 2 & 3 that would be helpful!

# Usage:  For all files in directory: $ Gsub.py [options] *.com/gjf
#         Or a single input file: $ Gsub.py [options] <input1>.com/gjf
#         Or multiple files separated by spaces: $ Gsub.py [options] <input1>.com/gjf <input2>.com/gjf ...
#  To get help or a list of the options run:$ [python] Gsub.py -h

# Updates:
# 2/14/2020: Dennis: script now includes h_vmem in resources needed on Hoffman2 since 2/13/2020
#

####################################################
#    ** Gaussian Hoffman2 submission scripts **    #
#   This script builds gaussian submission files   #
#    to submit to the hoffman2 cluster via the     #
#   SGE queuing system. (uses python 2.7.X)        #
####################################################
#     Currently, this script supports the use of   #
# Gaussian 16 revA.03 or Gaussian 09 revD.01       #
# future versions will be added when available     #
####################################################
# Script written Aug/2019 by Tyler from Houk group #
#    Updated last on 9/2019 by Tyler               #
####################################################
# Email Notification Settings                      #
#                                                  #
#  Set "send_email = 1" to enable email            #
#    notifications if desired. (0 = off)           #
#                                                  #
# email_options:                                   #
#  b=begin, e=ends, a=aborted, or 'bea' for all 3  #
#                                                  #
send_email = 1
email_options = "bea"
#                                                  #
# End of Email Notification Settings               #
####################################################
# Group Storage directory for checkpoint file      #
#group_storage = houk_group_storage/path           #
#   (coming soon!)                                 #
####################################################

import os
import os.path
import sys
import re
import time
from glob import glob
from optparse import OptionParser
import subprocess

##############################

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

##############################
# Works fully as long as route line is not more than one line!
def test_route(filename):
    # This calls the testrt gaussian utility to check if the route line is correct.
    #   The testrt utility needs the route line extracted from the .com file
    #     which is done by the following code. Then gaussian is loaded and
    #      the test is performed, and if route is good you should see the test pass.
    with open(filename) as file:
        lines = file.read().splitlines()
        for line in lines:
            if "#" in line:
                route = line
    cmdline = '. /u/local/Modules/default/init/modules.sh && module load gaussian && testrt "'
    cmdline += route
    cmdline += '"'
    print "command: ",cmdline
    print "route: ",route
    print "If the route shown above is not the full route then your input file has a route line that is more than 1 line and this won't work."
    print "  That does NOT mean you input is set up incorrectly. It's just a limitation of this script, use --test_job instead."
    print subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE).stdout.read()

##############################
# Works fully!
def test_job(g_filename, extension, chk_mem):
    # Test job adds %kjob l301 as a link0 command which kills the job after the link 301 program
    #   is finished, at which point the job has gotten to the point were the atoms/keywords are read
    #    and you can have a good idea if the calculation will run (atleast start) succesfully.
    #   This allows for a quick check before a full submission. This is done on the login node
    #    and thus you don't have to wait for a job to start in the queue to know if you set it up right.
    #       removes %mem, %nproc/%cpu, and %chk/%oldchk to make calculation easier.
    with open(g_filename + "_test_job"+ extension, "w") as newinput:
        newinput.write("%kjob l301\n")
    with open(g_filename + extension, "r") as input:
        with open(g_filename + "_test_job"+ extension, "a") as newinput:
            for line in input:
                if '%' not in line:
                    newinput.write(line)
                if '--link1--' in line or '--Link1--' in line:
                    print "--link1-- job found! This may cause an error due to keywords such as Geom=Check or Guess=Read and no checkpoint file to read, you can ignore these and the test will still pass for the first route section."
                    newinput.write(re.sub(r".*ink1--", "%kjob l301", line))
    cmdline = '. /u/local/Modules/default/init/modules.sh && module load gaussian && g16 '
    cmdline += g_filename + "_test_job"+ extension
    #cmdline += " > "+ g_filename + "_test_job.out" # this didn't work? a .log file is made instead.
    print subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE).stdout.read()
    with open(g_filename + "_test_job.log", "r") as logfile:
        lines = logfile.readlines()
        for line in lines:
            if " Normal termination" in line:
                print(bcolors.OKGREEN + "Gaussian job started succesfully; input file "+g_filename+" set up correctly and should be ready for full submission! " + bcolors.ENDC)
            if "primitive gaussians" in line:
                num_basis = line.split()[0]
            if " NAtoms=" in line and "NActive=" in line:
                num_atoms = line.split()[1]
    os.system("rm -f " + g_filename + "_test_job" + extension)
    print("The test job created a output file named " + g_filename + "_test_job.log, keep for further use or discard.")
    # the raw_input function is python2 compatible only, I cannot find a solution that works for both python 2 and 3.
    keepornot=raw_input("If you want to keep it type k or type d to discard: \n")
    if keepornot.lower() == "d":
        os.system("rm -f " + g_filename + "_test_job.log")
        print("discarding " + g_filename + "_test_job.log")
    else:
        print("keeping " + g_filename + "_test_job.log")
    if  chk_mem == True:
        print(bcolors.OKBLUE + "Using Gaussian freqmem utility to check memory requirements for the calculation based on number of atoms and number of basis functions:" + bcolors.ENDC)
        print("number of atoms: "+ num_atoms +" and number of basis functions: "+ num_basis)
        # Maybe We can just use one of these, they are fairly similar until the calculations get very large.
        openorclosed=raw_input("Are your calculations open-shell(unrestricted), type u or closed-shell(restricted), type r: \n")
        if openorclosed == "r":
            print "For closed-shell (restricted) Gaussian frequency calculations the memory requirements are:"
            cmdline2 = '. /u/local/Modules/default/init/modules.sh && module load gaussian && freqmem '
            cmdline2 += num_atoms + " " + num_basis + " r d > stdout"
            subprocess.Popen(cmdline2, shell=True, stdout=subprocess.PIPE)
            time.sleep(.5)
            with open("stdout", "r") as output:
                lines = output.readlines()
                for line in lines:
                    if "Minimum" in line:
                        min_memMW = float(line.split()[2])
                        min_memMB = str(min_memMW*8)
                        min_memGB = str(min_memMW*8/1024)
                        print("Minimum memory required for the calculation with up to D functions is "+ min_memMB +"MB or "+ min_memGB +"GB per core(or per thread).")
            cmdline2 = '. /u/local/Modules/default/init/modules.sh && module load gaussian && freqmem '
            cmdline2 += num_atoms + " " + num_basis + " r f > stdout1"
            subprocess.Popen(cmdline2, shell=True, stdout=subprocess.PIPE)
            time.sleep(.5)
            with open("stdout1", "r") as output:
                lines = output.readlines()
                for line in lines:
                    if "Minimum" in line:
                        min_memMW = float(line.split()[2])
                        min_memMB = str(min_memMW*8)
                        min_memGB = str(min_memMW*8/1024)
                        print("Minimum memory required for the calculation with up to F functions is "+ min_memMB +"MB or "+ min_memGB +"GB per core(or per thread).")
            cmdline2 = '. /u/local/Modules/default/init/modules.sh && module load gaussian && freqmem '
            cmdline2 += num_atoms + " " + num_basis + " r h > stdout2"
            subprocess.Popen(cmdline2, shell=True, stdout=subprocess.PIPE)
            time.sleep(.5)
            with open("stdout2", "r") as output:
                lines = output.readlines()
                for line in lines:
                    if "Minimum" in line:
                        min_memMW = float(line.split()[2])
                        min_memMB = str(min_memMW*8)
                        min_memGB = str(min_memMW*8/1024)
                        print("Minimum memory required for the calculation with up to H functions is "+ min_memMB +"MB or "+ min_memGB +"GB per core(or per thread).")
            os.system('rm stdout')
            os.system('rm stdout1')
            os.system('rm stdout2')
        else:
            print "For open-shell (unrestricted) Gaussian frequency calculations the memory requirements are:"
            cmdline2 = '. /u/local/Modules/default/init/modules.sh && module load gaussian && freqmem '
            cmdline2 += num_atoms + " " + num_basis + " u d > stdout"
            subprocess.Popen(cmdline2, shell=True, stdout=subprocess.PIPE)
            time.sleep(.5)
            with open("stdout", "r") as output:
                lines = output.readlines()
                for line in lines:
                    if "Minimum" in line:
                        min_memMW = float(line.split()[2])
                        min_memMB = str(min_memMW*8)
                        min_memGB = str(min_memMW*8/1024)
                        print("Minimum memory required for the calculation with up to D functions is "+ min_memMB +"MB or "+ min_memGB +"GB per core(or per thread).")
            cmdline2 = '. /u/local/Modules/default/init/modules.sh && module load gaussian && freqmem '
            cmdline2 += num_atoms + " " + num_basis + " u f > stdout1"
            subprocess.Popen(cmdline2, shell=True, stdout=subprocess.PIPE)
            time.sleep(.5)
            with open("stdout1", "r") as output:
                lines = output.readlines()
                for line in lines:
                    if "Minimum" in line:
                        min_memMW = float(line.split()[2])
                        min_memMB = str(min_memMW*8)
                        min_memGB = str(min_memMW*8/1024)
                        print("Minimum memory required for the calculation with up to F functions is "+ min_memMB +"MB or "+ min_memGB +"GB per core(or per thread).")
            cmdline2 = '. /u/local/Modules/default/init/modules.sh && module load gaussian && freqmem '
            cmdline2 += num_atoms + " " + num_basis + " u h > stdout2"
            subprocess.Popen(cmdline2, shell=True, stdout=subprocess.PIPE)
            time.sleep(.5)
            with open("stdout2", "r") as output:
                lines = output.readlines()
                for line in lines:
                    if "Minimum" in line:
                        min_memMW = float(line.split()[2])
                        min_memMB = str(min_memMW*8)
                        min_memGB = str(min_memMW*8/1024)
                        print("Minimum memory required for the calculation with up to H functions is "+ min_memMB +"MB or "+ min_memGB +"GB per core(or per thread).")
            os.system('rm stdout')
            os.system('rm stdout1')
            os.system('rm stdout2')
        print "Most frequency calculations may have optimal memory usage slightly above these minimum values."
        print "Note: frequency calculations are among the most memory hungry gaussian jobs so if it is enough memory for a frequency calculation it is plenty for a geometry optimization or single-point calculations."
        print "Remember that these are per-core values, meaning that you need multiply these values by the number of processors you use as memory usage scales linearly with processors used."
        print "Using less than these values may make memory the main bottleneck, processor cores will go unused and your calculations will be significantly slower."
        # 4GB per processor is recommended for calculations involving 50 or more atoms and/or 500 or more basis functions.
        # It is usually preferable to go above the minimum required amount to ensure optimal performance, between 2GB and 4GB per core is recommended. Though going higher than 4Gb per-core is needed for larger calculations there are few nodes available that have more than 5.25GB per core.
        #  You may also notice that these memory requirements can get very high (10-15GB per core) for large systems or large basis sets and at a point it is not feasible to use so much memory due to node limitation,
        #   in that case using 5GB per core would still be beneficial yet there are plenty of nodes available to allow for such high memory usage.


##############################
# Future: More gaussian utilities?
# freqchk?
# chkchk?
# formchk?
####################################

##################################################################

def write_subfile(subname, g_filename, extension, gaussian_version, nproc, time, mem, exclusive, verbose, follow, nosub):
    """
    Writes a SGE batch submission file which is submitted to the queue.
    subname (string): name of the submit file to be created
    g_filename: Gaussian input file
    walltime (integer): walltime for the job in hours (or HH:MM or HH:MM:SS)
    Also threads's are binded to cores and hyperthreading disabled for best performance on exclusive jobs.
    Ideally we would bind threads to cores in all jobs if we could figure out how to do so.
    """
    
    output = open(subname, 'w')
    # First we look at nproc and mem. Check if they are allowed and change them if they are not within allowable limits.
    int_ncpus = int(nproc)
    int_mem = int(mem)
    
    com_mem = str(mem)
    if exclusive == False:
        exclusive = "0"
        # less than 1GB per core will not be allowed.
        if int_mem < int_ncpus:
            com_mem=str(int_ncpus*2)
            int_mem=int_ncpus*2
        # more than 5.2GB per core will not be allowed
        if int_mem > int_ncpus*5.2:
            per_core = int_mem/int_ncpus
            print "Requesting "+str(per_core)+"GB per core seems excesive? Adjusting this down to a more reasonable 4GB per core..."
            print "This error is triggered whenever you attempt to submit a job with more than 5.2GB per core, since very few nodes have more than ~5.2GB per core"
            keepornot=raw_input("If this change is okay type c to continue, else any other key to abort and start over: \n")
            if keepornot.lower() == "c":
                com_mem=str(int_ncpus*4)
                int_mem=int_ncpus*4
                per_core = int_mem/int_ncpus
                print("Job is now requesting "+str(per_core)+"GB per core!")
            else:
                # If you have purposefully require a large amount of memory or custom settings that this script wont allow, remember you can run this script with the -n (nosub option)
                #  then manually adjust your input file and submission script to the values you desire and then submit via "qsub subscript_name.sh"
                print "Aborting...."
                print "   Note: Hoffman2 does not limit memory resource requests, submiting a job as you originally have, may still have been able to run, but either your job will suffer due to over requesting memory or you will be stealing resources form others (rude)."
                print "   For this reason if you require a large amount of memory, request an exclusive job (-x option) along with a higher memory request (i.e., -m 100  or whatever you think you will need)."
                print "     Or try again using allowable resource values..."
                quit()
    if int_ncpus == 1:
        sub_memMB = int(int_mem*1024)
        #com_mem = str(mem)
        # If greater than 4GB for just 1 core, you probably made a mistake, lets bring it back down to something reasonable.
        # For 1 core can choose from 1GB to 4GB, not higher or lower for now...
        if int_mem > 4:
            sub_memMB = 2048
            com_mem = str(2)
        sub_mem = str(sub_memMB+1024)
    else:
        sub_memMB = int(int_mem*1024)
        sub_mem = int((sub_memMB+1024)*(int_ncpus+1)/int_ncpus)
        intsub_mem = int(sub_mem)
        sub_mem = str(sub_mem/int_ncpus)
    ncpus = str(int_ncpus)
    if exclusive == 1:
        # Currently deciding if defaults should be lower for G09 to allow jobs to run on the smaller nodes
        #  since G09 can run on AMD nodes with 8/12-core and only 32ish GB
        #if gaussian_version == "G16A03" or gaussian_version == "G16A03SSE4":
        #increase the default ncpus for the following memory calculations.
        int_ncpus = 24
        ncpus = "This_will_be_updated_when_job_starts"
        # Default minimum is 60GB for all exclusive jobs since all nodes accessible by G16 have this much.
        if int_mem < 60:
            sub_mem = "60"
            com_mem = "55"
        else:
            # Leaving 5GB extra will occasionally cause job failures due to memory. leaving 7 GB extra seems okay, may need further adjustment?
            com_mem = str(int_mem-7)
            sub_mem = str(int_mem)
    time = str(time)
    number = time.count(":") + 1
    if number > 1:
        if number > 2:
            h, m, s = time.split(':')
            # print "hours and minutes and seconds given"
            time_s = int(h)*3600 + int(m)* 60 + int(s)
        else:
            # print "hours and minutes given"
            h, m = time.split(':')
            time_s = int(h)*3600 + int(m)*60
    else:
        # print "only hours given"
        h = time
        time_s = int(h)*3600
    h_walltime = str(time_s)
    # get s_rt=## (soft runtime limit) to generate a signal to warn us the time is scheduled to timeout in 10 seconds.
    int_time = int(time_s)
    s_walltime = str(int_time-10)
    if int_time > 1209600:
        print "Too much time requested! Setting time to maximum allowed: 336 hours."
        int_time=1209600
        h_walltime = str(int_time)
        s_walltime = str(int_time-10)
        print "Walltime limit is: "+h_walltime+" and soft walltime alert is sent at: "+s_walltime
    highp = "0"
    if int_time > 86400:
        highp = 1
        print "highp job detected(>24 hours)! Submitting to Houk nodes only!"
    # Edit input file. %nproc is replaced with %cpu when exclusive. This is done via
    #  the submit script because we need to find out the processor count after
    #   the node has been allocated for the job.
    # TODO: add %chk=checkpointfile.chk if none is already being used.
    with open(g_filename + "_temp" + extension, "w") as newinput:
        newinput.write("%nproc="+ncpus+"\n")
        newinput.write("%mem="+com_mem+"GB\n")
    with open(g_filename + extension, "r") as input:
        with open(g_filename + "_temp" + extension, "a") as newinput:
            for line in input:
                if "%nproc" not in line and "%cpu" not in line and "%mem" not in line:
                    newinput.write(line)
                if '--link1--' in line or '--Link1--' in line:
                    print "--link1-- job found! Carefully updating second link 0 keywords"
                    newinput.write(re.sub(r".*ink1--", "%nproc="+ncpus+"\n%mem="+com_mem+"GB ", line))
    os.rename(g_filename + "_temp" + extension, g_filename + extension)
    print "Updated input file!"
    ###############################################################
    # Set up submit script
    output.write("#!/bin/bash -l\n")
    output.write("#$ -cwd\n")
    
    # Different versions of Gaussian can run on different node architectures and the following lines are needed.
    #if gaussian_version == "G16A03" or gaussian_version == "FUTURE": *Future versions will likely mimic the requirements of G16A03
    if gaussian_version == "G16A03":
        if exclusive == 1:
            if highp == 1:
                output.write("#$ -l exclusive,h_data=" + str(sub_mem) +'G,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'G,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",highp,arch=intel-[Eg][5o][l-]*\n")
            else:
                output.write("#$ -l exclusive,h_data=" + str(sub_mem) +'G,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'G,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",arch=intel-[Eg][5o][l-]*\n")
        else:
            if highp == 1:
                output.write("#$ -l h_data=" + str(sub_mem) +'M,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'M,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",highp,arch=intel-[Eg][5o][l-]*\n")
            else:
                output.write("#$ -l h_data=" + str(sub_mem) +'M,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'M,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",arch=intel-[Eg][5o][l-]*\n")
            output.write("#$ -pe shared* "+str(nproc)+"\n")
    elif gaussian_version == "G16A03SSE4":
        if exclusive == 1:
            if highp == 1:
                output.write("#$ -l exclusive,h_data=" + str(sub_mem) + 'G,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'G,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",highp,arch=intel*\n")
            else:
                output.write("#$ -l exclusive,h_data=" + str(sub_mem) + 'G,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'G,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",arch=intel*\n")
        else:
            if highp == 1:
                output.write("#$ -l h_data=" + str(sub_mem) + 'M,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'M,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",highp,arch=intel*\n")
            else:
                output.write("#$ -l h_data=" + str(sub_mem) + 'M,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'M,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",arch=intel*\n")
            output.write("#$ -pe shared* "+str(nproc)+"\n")
    elif gaussian_version == "G09D01":
        if exclusive == 1:
            if highp == 1:
                output.write("#$ -l exclusive,h_data=" + str(sub_mem) +'G,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'G,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",highp\n")
            else:
                output.write("#$ -l exclusive,h_data=" + str(sub_mem) +'G,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'G,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + "\n")
        else:
            if highp == 1:
                output.write("#$ -l h_data=" + str(sub_mem) + 'M,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'M,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + ",highp\n")
            else:
                output.write("#$ -l h_data=" + str(sub_mem) + 'M,h_vmem='+ str(float(sub_mem)*int(nproc)) + 'M,h_rt='+ str(h_walltime) + ",s_rt="+ str(s_walltime) + "\n")
            output.write("#$ -pe shared* "+str(nproc)+"\n")
    # Trapping the signal SIGUSR1 on hoffman seems to not need -notify option, works the same with or without it. (SO what is it used for?)
    #output.write("#$ -notify -l s_rt="+ str(s_walltime) + "\n") # sends a singal, SIGUSR1, at the s_rt=time set 30 seconds before time out
    output.write("#$ -j y\n")
    output.write("#$ -o joblog." + g_filename + ".$JOB_ID\n")
    if send_email == 1:
        output.write("#$ -M $USER@mail\n")  # no need to change email address, hoffman2 knows your email.
        output.write("#$ -m " + email_options + "\n") # Only change email settings in the email box at the top, not here.
    output.write("\n")
    output.write("\n")
    output.write("############################################################################\n")
    output.write("#                                                                          #\n")
    output.write("###################### qsub script for Gaussian job ########################\n")
    output.write("#                                                                          #\n")
    output.write("############################################################################\n")
    output.write("# Write no bash commands above this hash box!\n")    # Only SGE settings above here.
    output.write("\n")
    if gaussian_version == "G16A03":
        output.write(". /u/local/Modules/default/init/modules.sh\n")
        output.write("module load gaussian/g16_avx\n")
        output.write("exe=`which g16`\n")
    elif gaussian_version == "G16A03SSE4":
        output.write(". /u/local/Modules/default/init/modules.sh\n")
        output.write("module load gaussian/g16_sse4\n")
        output.write("exe=`which g16`\n")
    # Add future versions of gaussian here!
    # elif gaussian_version == "GFUTURE":
    elif gaussian_version == "G09D01":
        output.write("export g09root='/u/local/apps/gaussian/09d01'\n") # No module file for G09D01 unlike the others...
        output.write(". $g09root/g09/bsd/g09.profile\n")
        output.write(". /u/local/Modules/default/init/modules.sh\n")
        output.write("module load intel\n")
        output.write("exe=`which g09`\n")
    output.write("\n")
    output.write("\n")
    output.write("export GAUSS_SCRDIR=$TMPDIR\n")
    output.write("\n")
    output.write("set echo\n")
    output.write("\n")
    output.write("\n")
    output.write("chkpointfile=`grep -h '%chk=' " + g_filename + extension + " | sed -e 's/%chk=//'`\n")
    output.write("oldchkpointfile=`grep -h '%oldchk=' " + g_filename + extension + " | sed -e 's/%oldchk=//'`\n")
    output.write("echo $chkpointfile\n")
    output.write("echo $oldchkpointfile\n")
    output.write("\n")
    output.write("submitdir=`pwd`\n")
    output.write("tempdir=$GAUSS_SCRDIR\n")
    output.write("chkstoragedir=$submitdir/checkpoints\n")
    output.write("\n")
    output.write("\n")
    output.write("\n")
    output.write("\n")
    # Function coming soon! Once our group storage is up and running...
    #if use_storage == True:
        # This function allows to take advantage of the extra storage by sending the checkpoint files to it.
        #  First we cut the $HOME path from current directory, specific for user and job(s).
        #  Ex: if current directory is ~/cycloadditions/6plus4/wB97xd/ this will strip /cycloadditions/6plus4/wB97xd/ from ~/
        #   to create a mirror of the current directory in our group storage as group_storage/cycloadditions/6plus4/wB97xd/.
        #  This should make keeping track of these files easier and to not fill up users home. No more excuse to not keep these.
        #  If the user moves the checkpoint then the alternative is to keep the checkpoint in the current submission directory.
        #   This script will check both locations, and if the file is in neither the calculation won't able to read from it if needed.
        #output.write("chkstoragedir_path=`echo $PWD | sed "s:^$HOME::"`\n")   # Add current sub directory to our storage directory to keep things tidy.
        #output.write("alt_chkstoragedir="+group_storage+"/$USER/$chkstoragedir_path/\n")
        #output.write("mkdir -p $alt_chkstoragedir\n")
        #output.write("chkstoragedir=$alt_chkstoragedir\n")
    # else:
    #     output.write("mkdir -p $chkstoragedir/\n")
    output.write("\n")
    # Make our on-node temp/scratch dir and send input file to it. This is recommended as it is cleaner, faster, and reduces I/O overhead for you and others users.
    output.write("mkdir -p $tempdir/\n")
    output.write("mkdir -p $chkstoragedir/\n")
    output.write("\n")
    output.write("cp " + g_filename + extension + " $tempdir/\n")
    output.write("cp $chkstoragedir/$chkpointfile $tempdir/\n")  # To load or restart from a previous checkpoint file and if .chk is stored in the storage dir, this will be needed.
    output.write("cp $chkstoragedir/$oldchkpointfile $tempdir/\n") # Ditto as above if reading in from %oldchk, both will ignore it of course if no chk file exists.
    output.write("cp $submitdir/$chkpointfile $tempdir/\n")  # incase the chkpoint file is in current directory.
    output.write("cp $submitdir/$oldchkpointfile $tempdir/\n") # ditto
    output.write("\n")
    output.write("echo ignore any possible errors above this line. \n")
    output.write("echo --------------------------------------------- \n")
    output.write("echo Cluster and node setup information:\n")
    output.write("echo current directory is: `pwd`\n")
    output.write("echo temp working directory is: $TMPDIR\n")
    # Submitting job from our local on-node super fast storage and avoid network I/O
    output.write("cd $tempdir/\n")
    output.write("\n")
    output.write("echo now we have moved into temp directory: `pwd` \n")
    output.write("echo      job ID is: $JOB_ID\n")
    output.write("echo      job name is: $JOB_NAME\n")
    output.write("echo      job hostname is: $HOSTNAME\n")
    output.write("echo  PE hostfile name is: $PE_HOSTFILE\n")
    output.write("echo If it exists, PE hostfile is shown below:\n")
    output.write("cat $PE_HOSTFILE\n")
    output.write("\n")
    output.write("\n")
    output.write("\n")
    output.write("\n")
    # The main necessity for this is ensuring the checkpoint file finds its way back home and cleaning up, incase job doesn't complete normally.
    #   If the job aborts or is terminated abnormally the commands following the exe of gaussian are not executed, this function fixes that.
    #  However, there are other advantages to getting a warning before the job aborts.
    #  Within this function you can add your own commands or call personal scripts.
    #   For instance when the job is about to time out you can call a script that will regenerate an input file
    #    then resubmit the job. (see example below)
    output.write("# catch the SIGUSR1 signal with our cleanup function\n")
    output.write("_cleanup() {\n")
    output.write("  echo --------------------------------------------- \n")
    output.write("  echo the current working directory is `pwd`\n")
    output.write("  echo job "+ g_filename +" -ID:$JOB_ID- received SIGUSR1 at $(date).\n")
    output.write("  echo job "+ g_filename +" is nearly timed out so cleaning things up before deletion.\n")
    output.write("  echo The job has run out of time on: $(date)\n")
    output.write("  ENDTIME=$(date +%s)\n")
    output.write("  echo Overall the job has run for $(($ENDTIME - $STARTTIME)) seconds.\n")
    output.write("  echo --------------------------------------------- \n")
    output.write("  cp $chkpointfile $chkstoragedir/\n")
    output.write("  cd $submitdir/\n")
    # Example:    ("  newinput=`sh ~/bin/auto_regeninput.sh " + g_filename + ".com`) # This script would generate a new input file (ideally reading in from the previous checkpoint). It would then print/output (echo name) the new input file name (hence newinput=...).
    # Example:    ("  echo new input file $newinput has been created and is ready to submit)
    # Example:    ("  echo job $newinput is submitted at $(date))
    # Example:    ("  python ~/bin/Gsub.py $newinput) # submit the new input file
    output.write("  echo successfully cleaned up before everything was deleted!\n")
    output.write("}\n")
    # output.write("\n")
    output.write("trap _cleanup SIGUSR1\n") # trap the SIGUSR1 signal and cleanup before job is terminated and files are lost.
    # output.write("trap _cleanup SIGTERM\n") # This signal arrives whenever a "qdel" command is issued? or so it says online...
    # I think the custom SIGUSR1 warning is preferred.
    # Options: SIGHUP SIGINT SIGQUIT SIGTERM SIGUSR1
    output.write("\n")
    output.write("echo --------------------------------------------- \n")
    output.write("\n")
    output.write("node_memGB=`cat /proc/meminfo | awk '/MemTotal:/ {print $2/1024/1024 \"GB\"}'`\n")
    output.write("node_cpus=`nproc`\n")
    output.write("node_arch=`qhost -h $HOSTNAME | awk '/^n/ {print $2}'`\n")
    output.write("\n")
    output.write("\n")
    if exclusive == 1:
        output.write("echo Exclusive Job! \n")
        output.write("ncpus=`lscpu | awk '/^On-line/ {print $4}'`\n")
        output.write("inp_memGB=`cat /proc/meminfo | awk '/MemTotal:/ {printf (\"%dGB\\n\", $2/1024/1024-7)}'`\n")
        output.write("\n")
        output.write("echo We have been allocated a node with $node_cpus cores available and $node_memGB of RAM.\n")
        output.write("echo - altering input file to enable core binding by utilizing the keyword: %cpu=$ncpus \n")
        output.write("echo - also increasing the memory in the input file to $inp_memGB leaving some spare room for Gaussian and I/O overhead. \n")
        output.write("sed -i 's/'%nproc.*'/'%cpu=$ncpus'/g' " + g_filename + extension + "\n")
        output.write("sed -i 's/'%mem.*'/'%mem=$inp_memGB'/g' " + g_filename + extension + "\n")
    output.write("\n")
    output.write("echo Hoffman2 "+ gaussian_version +" calculation of "+ g_filename +" on node: $HOSTNAME\n")
    if exclusive == 1:
        output.write("echo This job requested all resources on a node with at-least " + str(sub_mem) + "GB RAM using the exclusive keyword.\n")
        output.write("echo  - We are allocated node $HOSTNAME, an $node_arch system with $node_memGB of total RAM and $node_cpus processors.\n")
        output.write("echo This job will use all $node_cpus cpu cores, using optimal core binding while preventing hyperthreading.\n")
        output.write("echo The input file has been modified to include %cpu=$ncpus and %mem=$inp_memGB RAM for the calculation.\n")
    else:
        output.write("echo This job requested " + str(ncpus) + "-cpu cores and " + str(sub_mem) + "MB of RAM per core.\n")
        output.write("echo  - We are allocated node $HOSTNAME, an $node_arch system with $node_memGB of total RAM and $node_cpus processors.\n")
        output.write("echo For the calculation, in the input file we requested " + str(ncpus) + "cpu cores and " + str(com_mem) + "GB total RAM.\n")
    output.write("echo --------------------------------------------- \n")
    output.write("echo The job started on: $(date) \n")
    output.write("STARTTIME=$(date +%s)\n")
    output.write("\n")
    output.write("\n")
    if verbose == "3":
        output.write("echo '  Time     PID    COMMAND     CPU%    MEM%   VIRT    RES   SHR' > $submitdir/top.log." + g_filename + ".$JOB_ID\n")
        output.write("\n")
        output.write("/usr/bin/time -v -a $exe < " + g_filename + extension + " >  $submitdir/" + g_filename + ".out &\n")
        output.write("done=$!\n")
        # Sleeping 2 seconds is needed to allow Gaussian to start in order to get the l###.exe PID to monitor it.
        # The top delay (-d 1) can be changed to any number, currently it is 1 second (probably overkill) which outputs the data from top every second and the data is an average of usage over the last second.
        #  A delay of 5 or 10, averaging over each 5/10 seconds, would generate sufficiently accurate data over time as well without creating too big of a file with too much data.
        #    Having a delay larger than 10 seconds is not recommended as it can easily overlook large spikes (high or low) in usage.
        output.write("sleep 2s && top -b -d 1 -p $(pgrep -f l*.exe -u $USER) | awk -v OFS=\"   \" '$1==\"top\"{ time=$3 } $1+0>0 { print time,$1,$NF,$9,$10,$5,$6,$7; fflush() }' >> $submitdir/top.log." + g_filename + ".$JOB_ID &\n")
        output.write("disown\n")
        output.write("wait $done\n")
        output.write("pkill -P $$\n")
    else:
        output.write("\n")
        output.write("/usr/bin/time -v -a $exe < " + g_filename + extension + " >  $submitdir/" + g_filename + ".out &\n")
        output.write("wait\n")
    output.write("\n")
    output.write("\n")
    output.write("echo The job finished on: $(date)\n")
    output.write("ENDTIME=$(date +%s)\n")
    output.write("echo Overall the job took $(($ENDTIME - $STARTTIME)) seconds.\n")
    output.write("echo --------------------------------------------- \n")
    output.write("\n")
    output.write("\n")
    # Send completed .chk to the dir where you submitted from originally and return there before cleaning up.
    output.write("cp $chkpointfile $chkstoragedir/\n")
    # output.write("cp " g_filename + ".rwf $chkstoragedir/\n") # If needed, we can save .rwf for better job restarting. Files get very large so do this only if needed.
    output.write("cd $submitdir/\n")
    output.write("\n")
    # clean up. This should be done automatically anyway, but just incase it is polite to do.
    output.write("rm $tempdir/*\n")
    output.write("rmdir $tempdir/\n")
    output.write("echo Job finished at:\n")
    output.write("date\n")
    output.write("\n")# Number of processors reduced to   1 by ecpmxn."  " PrsmSu:  requested number of processors reduced to:   1 ShMem   1 Linda."  " CalDSu:  requested number of processors reduced to:   5 ShMem   1 Linda."
    # Should we also look for "Number of processors reduced to"? It seems it sometimes could be either?
    output.write("if core_chk=`grep 'requested number of processors reduced' " + g_filename + ".out`; then\n")
    output.write("  echo $core_chk\n")
    output.write("  better_val=`echo $core_chk | awk '{print $9}'` \n")
    output.write("  echo Job was limited to $better_val cores, use more memory or reduce the number of processors used to $better_val for best performance!\n")
    output.write("fi\n")
    output.write("\n")
    output.write("\n")
    if verbose == "2" or verbose == "3":
        output.write("echo --------------------------------------------- \n")
        output.write("echo Job accounting information:\n")
        output.write("qstat -F -j $JOB_ID\n")
        output.write("\n")
        output.write("\n")
        output.write("echo ""\n")
        output.write("echo ""\n")
        output.write("echo --------------------------------------------- \n")
        output.write("echo Node accounting information:\n")
        output.write("echo  *note: if not using exclusive there likely were other jobs running on this node running alongside your job.\n")
        output.write("echo ""\n")
        output.write("qhost -F -h $HOSTNAME\n")
        output.write("\n")
    output.write("\n")
    output.write("echo ""\n")
    output.write("echo Done!\n")
    output.write("echo --------------------------------------------- \n")
    if follow != 0:
        # a few different versions depending on goals of its usage.
        # sending stdout and stderr to /dev/null if the script/command to run has its own ouput (i.e. goodvibes)
        #output.write("qsub -hold_jid $JOB_ID -V -cwd -o /dev/null -e /dev/null -j y -b y " + follow + " &\n")
        # option -b y makes qsub expect a binary to execute (python or bash commands like rm, mv, etc,..), I am not sure what exactly qualifies as non-binary, a text based script (script.sh) perhaps?
        output.write("qsub -hold_jid $JOB_ID -V -cwd -j y -b y " + str(follow) + " &\n")
        #output.write("qsub -hold_jid $JOB_ID -V -cwd -j y " + follow + " &\n")
        output.write("wait\n")
    output.write("################### Job Ended ###################\n")
    # function to delete the joblog, only if job completed successfully (regardless of normal termination in gaussian)
    if verbose == "0":
        output.write("qalter -o /dev/null -e /dev/null -j y $JOB_ID &\n")
        output.write("qsub -hold_jid $JOB_ID -cwd -o /dev/null -e /dev/null -b y rm joblog." + g_filename + ".$JOB_ID 2>&1 >/dev/null &\n")
        output.write("wait\n")
    output.write("exit 0\n")
    output.close()


##################################################################

extra_help="""
Example with current defaults and no options submitting via:$ python Gsub.py *.com
  This would submit all .com files in directory, requesting 8cpus, 16GB ram, and 24 hours.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
"""+ bcolors.HEADER +"""
  -p NPROC, --nproc=NPROC """ + bcolors.ENDC + """
                        Enter the number of processors to be used (default 8).
                        This will override and replace what is in input file.
                        Jobs will take longer to start the more you ask for.

* Nproc can be up to 36-cores(+ a few larger nodes), the more cores requested the potentially longer queue time.
   Here is a summary of the nodes available on the hoffman2 cluster (as of Aug/2019):
          144 nodes with 36 processors
          12 nodes with 72 processors   (< unlikely gaussian jobs will need these)
          9 nodes with 32 processors
          136 nodes with 24 processors
          236 nodes with 16 processors
  ^ G16A03 can use most of the 16-core nodes in addition to all the nodes above(all 24-72core nodes)
          341 nodes with 12 processors
          460 nodes with 8 processors
  ^ In addition to all nodes G16AO3 uses, G16A03SSE4 can use most of the 12-core nodes and ~half the 8 core nodes.
  ^ G09 can use all ~1330 of the nodes listed above.
"""+ bcolors.HEADER +"""
  -t TIME, --time=TIME  """ + bcolors.ENDC + """
                        Enter the walltime in hours for the calculation, enter
                        a number 1 to 336.(default 24). If 24 or less, job
                        will submit to all shared nodes. For more control you can
                        request time using the format HH:MM or HH:MM:SS. For example,
                        to request 30 minutes you can use 00:30 or for 59 seconds
                        you can use 00:00:59. Formatting is important for these to
                        work correctly (:30 for 30 minutes will not work). Also,
                        be aware that going 1 second over 24 hours will require highp
                        (24:00:01) and likewise using 336:00:01 would be over the
                        maximum time limit.

* Walltime is in hours, can be 1 to 336. If more than 24 hours the 'highp' keyword is added (this is mandatory for the job to run).
    With the highp option (>24 hours) the jobs are limited to only the 30 available Houk nodes, which may increase queue wait time.
"""+ bcolors.HEADER +"""
  -m MEM, --mem=MEM     """ + bcolors.ENDC + """
                        Enter the total shared memory for the calculation in
                        GBs, as would be in your Gaussian input file.
                        2GB per core, the default, is safest for shortest
                        queue waits, as all nodes have access to this amount.
                        2GB per core is automatically used if -m # is not used
                        but -p # is. Using -m overrides this default, unless
                        you try requesting less than 1GB per core, then it
                        defaults back to 2GB per core. Using -p 1 (1 processor)
                        the default mem is 1GB, but you can use the -m option to
                        ask for up to 4GB. Requesting more than 4GB per core is
                        not recommended as it will likely cause a longer queue wait
                        time and not benefit your calculation. Max of 4GB is the
                        recommended amount for best performance on large calculations.
                        Using more than 5.2GB per core is entirely disallowed as
                        only a handful of nodes have this much memory and if your
                        job runs it will not know to use the large memory nodes
                        and then it will either suffer due to the over requesting
                        the resources or it will steal the resources from someone
                        else's job (which is very rude). If more than 5.2GB per core
                        is requested it will be changed to 4GB per core automatically.
  Example:
    Submitting via $ python Gsub.py -p 24 *.com
       Would submit all .com files in directory, requesting 24cpus, 48GB ram, and 24 hours.
    Submiting via $ python Gsub.py -p 24 -m 1 *.com
       Would still submit all jobs requesting 24 cpus and 48GB ram, overriding your request for only 1GB.
    Submiting via $ python Gsub.py -p 2 -m 20 *.com
       Requesting 2 cpus and 20GB ram (10GB per core) is too much memory, the script will lower this
       to use a reasonable 4GB per core. If you need large amounts of RAM use exclusive jobs.
    For serial jobs, submitting via $ python Gsub.py -p 1 *.com
       Would submit all .com files in directory, requesting 1cpu core, 1GB ram, and 24 hours.

 * Note: 4GB of ram per core is the recommended amount for gaussian jobs, but not all nodes have
   4GB per core. Every node has at-least 2.5GB per core so using 2GB per core for the calculation
   is the best compromise for between for shortest possible queue wait time and job performance.
 Using at least 4GB per core is still recommended for larger jobs (50 atoms or 500 basis functions and up)
   even though the jobs 'may' take longer to start. For very large frequency calculations and for
    large CCSD and EOM-CCSD energies, it is also desirable to leave enough memory to buffer
     the large disk files involved. Therefore, a Gaussian job should only be given 50-70% of the
     total memory on the system. For example, on a machine with a total of 128 GB, one should
     typically give 64-80 GB to a job which was using all the CPUs, and leave the remaining memory
       for the operating system to use as disk cache. This requirement is very rarely encountered.
"""+ bcolors.HEADER +"""
  -d, --discard       """ + bcolors.ENDC + """
                        Use option --discard (or -d) to delete qsub submission
                        files after submission to queue (default False).
"""+ bcolors.HEADER +"""
  -g gaussian_version, --gaussian=gaussian_version """ + bcolors.ENDC + """
                        Enter the version of gaussian to be used. Options:
                        G16A03 G16A03SSE4 or G09D01 (default G16A03).
                        G16A03(default) uses the AVX instruction set which is
                        recommended for performance, but it is limited to a
                        subset of nodes(526 nodes)(though these are the newest
                        and fastest nodes). G16A03SSE4 uses the SSE4 instruct
                        set and is slower but can be used on about twice as
                        many nodes(1058) (potentially lower queue time). G09
                        has access to about 25% more nodes than G16A03SSE4
                        (1330 nodes)(potentially even lower queue wait time,
                        but the additional nodes are the oldest and
                        slowest.).
  """+ bcolors.WARNING + """                        (Make sure to use all caps!).""" + bcolors.ENDC + """
"""+ bcolors.HEADER +"""
  -r, --test_route      """ + bcolors.ENDC + """
                        Use option --test_route (or -r) to test the route line
                        for input files using the gaussian(G16) utility, does not
                        submit to queue (default False). This will give you
                        confirmation that your route line including keywords,
                        method/functional, and basis sets are set up correctly.
                        Currently, it does not work if you route line is more
                        than 1 line long. This can be used for multiple input
                        files, i.e., Gsub.py -r *.com
"""+ bcolors.HEADER +"""
  -k, --test_job       """ + bcolors.ENDC + """
                        Use option --test_job (or -k) to quickly test gaussian
                        input files using gaussian (G16); by starting a calculation
                        but will kill the job after link 301 finishes (about 1
                        second into the calculation). Does not submit to
                        queue (default False). Once the calculation successfully
                        starts and finishes you will be prompted if you want to
                        keep or discard the XXX_test_job.log gaussian output file.
                        You may generally discard these but this output can have
                        useful information for other uses if desired.
                        This can be used for multiple input files: Gsub.py -k *.com
                        This will cause errors if the input attempts to read from
                        checkpoint file such as using Geom=Check or Guess=Read
                        because we won't have a checkpoint for the test job.
"""+ bcolors.HEADER +"""
  -c, --check_memory   """ + bcolors.ENDC + """
                        Use option --check_memory (or -c) to quickly check the
                        minimum memory requirements for gaussian frequency
                        calculations. This will first test the gaussian input
                        files using gaussian (via --test_job (or -k));
                        providing us with the number of basis functions for
                        the freqmem gaussian utility. This will then print the
                        memory requirements (in MB) you can use as a estimate
                        for the minimum amount of memory PER core to request
                        for optimal computational resource usage. Does not
                        submit to queue (default False).
"""+ bcolors.HEADER +"""
  -n, --nosub           """ + bcolors.ENDC + """
                        For testing, use option --nosub (or -n) to create
                        submission files but don't submit to queue (default
                        False). This will alter the gaussian input files to
                        reflect the processor count and memory requested,
                        using the default 8-core, 16GB mem settings if none
                        (no -p/-m) is provided. This option can also be used
                        to add or change %nproc and %mem lines for input files
                        if desired and if that is your only goal also use
                        option -d to also discard the submission files. If your
                        calculation requires special or additional submission
                        script options you can use this option to generate the
                        submission script files, alter them as needed, then
                        submit them via: qsub input_filename.sh
"""+ bcolors.HEADER +"""
  -x, --exclusive       """ + bcolors.ENDC + """
                        Use option --exclusive (or -x) to reserve a whole node
                        for the calculations, job will check the resources
                        available on the node and use all of it by default.
                        (default False). This will override the input of -p or
                        --nproc to ensure jobs always use the whole node.

* Using Exclusive requests a full node regardless of the number of processors,
   this flexibility allows for shorter queue waiting times and more efficient use of resources.
 Once a job starts the submit script will find out how many processors and amount of memory
   are available on the allocated node and then the input file is automatically updated making use of the
   full node by using the recommended %cpu=#-# setting and changing the memory requested.
   - The updated memory provided in the input file will always be ~ 7GB less to ensure spare
       resources are available for gaussian and other system I/O processes for job to run safely.
            (i.e, If the node has 64 GB, gaussian will be allowed to use up to ~57GB)
 For exclusive, G16A03 is limited to 16-core nodes and up. G16A03SSE4 can run on 8-core and up nodes.
  By using exclusive the script will request a node with atleast 60GB of memory which covers every node
   that G16AO3 can run on, if the node has more memory the job will of course make use of it.
  If you want to make sure you get a node with more than 60GB of memory for certain jobs then simply
    request it via the -m ##GB option in combination with -x (exclusive) option. Values less than 60GB are ignored.

  Example:
    Submitting via $ python Gsub.py -x -m 120 *.com
       Would submit all .com files in directory, requesting whole nodes that have at least 120GB of memory or more.
       And once the node is allocated, the input file will be altered to 7GB less than the node has.
            For instance if a node with 128GB is allocated the input file will then receive 121GB.
"""+ bcolors.HEADER +"""
  -V VERBOSE, --Verbose=VERBOSE """ + bcolors.ENDC + """
                        Enter a number, either 0, 1, 2, or 3 corresponding to
                        the level of verbose job logging output you would like
                        (default is 1).
    Using option -V 0 provides nothing, and joblog file is deleted for successful jobs, 1 includes minimal
        information via the /usr/bin/time utility, 2 additionally outputs the SGE job and node accounting
        information, and 3 additionally collects full CPU/MEM data for the duration of the calculation, useful for
        closely monitoring calculation performance or plotting resource usage statistics.
 """+ bcolors.HEADER +"""
  -f FOLLOW, --follow_up=FOLLOW""" + bcolors.ENDC + """
                        Execute command or script when the calculation finishes
                        successfully.

    Calling a script with multiple spaced separated arguments must be in quotes (as per examples).
    Complex scripts can be called from current directory or via full path (-f ./myscript.sh or -f ~/bin/myscript.sh ),
         and within ./myscript.sh you can use multiple functions or call other scripts as usual.
    For instance, a complex script could check an .out file for normal termination, extract the coordinates,
        build an new single point input file, and submit the calculation.

    Example bash command:$ python Gsub.py -f ./job_check.sh *.com
      Which would execute the fictional job_check script after each .com calc finishes.

    OR:$ python Gsub.py -f "echo calculation finished >> ./job_monitor.txt" job.com
       This would print 'calculation finished' to a job_monitor file when job.com is finished.

    OR python example:$ python Gsub.py -f "python -m goodvibes *.out" *.com
      This would submit all .com files in the current directory and as each job finishes successfully
       (Hoffman2/SGE job, not necessarily normal termination of gaussian job) the goodvibes script is run.
      By default goodvibes outputs the data to a file such as goodvibes_output.dat which will be overwritten
       and updated as each job finishes, and including every output file in the directory (due to the *.out).
      The script/module, such as goodvibes, must first be installed and working properly in your home environment.

 * Submitting the above commands work as described but it also creates an SGE stdout file that can sometimes be
  unwanted, especially when the script used creates its own output. You can get rid of stdout by sending it to
  /dev/null before the script is called, for example:$ python Gsub.py -f "-o /dev/null python -m goodvibes *.out" *.com
 * Note aliases will not be understood and some limitations may apply.
     You should test this feature before using in production runs, use at your own risk!
                        """+ bcolors.HEADER +"""
  -s, --storage         """ + bcolors.ENDC + """
                        Use option --storage (or -s) to turn off the use of
                        group storage for saving checkpoint files. By default
                        these files are saved to our group storage and read it
                        from there if the calculation is set to read from a
                        checkpoint file. Using this option will have the
                        checkpoint saved to the current submission directory.
                        (default True). COMING SOON
"""+ bcolors.HEADER +"""
  -H, --extra_help      """ + bcolors.ENDC + """
                        Use option --extra_help (or -H) to get much more
                        detailed help for all of the options. (default False).

------------------------------------------------------------------
Notes specifically regarding the Hoffman2 computing cluster and Houk nodes:

* No Houk node has more than 5.3GB per core, so never ask for more than 5.3GB per core with highp (job longer than 24 hours).
  Keep in mind only 7 Houk nodes have more than 4GB per core (5.3GB max). Many Houk nodes have less than 4GB per core (13 out of 30)
    so be considerate using highp (or more than 24 hours) for jobs that will take 4GB per job or greater.

 * Using the highp keyword doesn't guarantee your job will start quicker. Due to normally high demand for Houk nodes,
   it is likely a job will start sooner if not using highp and even if having to resubmit the job after 24 hours
     your job may finish quicker overall rather then waiting for Houk nodes to become available.

This script also handles moving checkpoint files to the node for the calculation,
   and moving it back after the calculation. It will handle the use of %oldchk as well
   to read from an old checkpoint but write to a new one. To not take up space in your home directory the
   checkpoint files are saved in the group storage by default. If you have moved the checkpoint file out
   of this directory you can place it in the submission directory so that this script can find it.
------------------------------------------------------------------
"""

###############################################################################
# Getting user arguments first. Code adapted from goodvibes and other scripts #
###############################################################################
def main():
    # get command line inputs. Use -h to list all possible arguments and default values
    parser = OptionParser(usage=bcolors.HEADER + " For all files in directory:" + bcolors.ENDC + " $ %prog [options] *.com (or *.gjf)   "
                          + bcolors.HEADER + "\n        Or a single input file:" +
                          bcolors.ENDC + " $ %prog [options] <input1>.com/gjf  "
                          + bcolors.HEADER + "\n        Or multiple files separated by spaces:" + bcolors.ENDC + " $ %prog [options] <input1>.com <input2>.com ...", version="%prog 0.5 beta")
    parser.add_option("-p", "--nproc", dest="nproc", action="store",
                      help="Enter the number of processors to be used (default 8). This will override and replace what is in input file.", default=8)
    parser.add_option("-t", "--time", dest="time", action="store",
                      help="Enter the walltime in hours for the calculation, enter a number 1 to 336.(default 24). If >24 hours, highp option is automatically added. (optional format HH:MM or HH:MM:SS) ", default=24)
    parser.add_option("-m", "--mem", dest="mem", action="store", help="Enter the total shared memory for the calculation in GBs, as would be in your Gaussian input file. 2GB per core is the default as calculated via nproc*2. Using -m overrides this default, unless you try requesting less than 1GB per core, then it defaults back to 2GB per core. ", default=1)
    parser.add_option("-d", "--discard", dest="discard", action="store_true",
                      help="Use option --discard (or -d) to delete qsub submission files after submission to queue (default False).", default=False)
    parser.add_option("-g", "--gaussian", dest="gaussian_version", action="store", help="Enter the version of gaussian to be used. Options: G16A03 G16A03SSE4 or G09D01 (default G16A03). G16A03(default) uses the AVX instruction set which provides the best performance, but fewer nodes are available to run it."
                      + bcolors.WARNING + "(Must use all caps!)" + bcolors.ENDC + ".", default="G16A03SSE4", choices=['G16A03', 'G16A03SSE4', 'G09D01',] , metavar="gaussian_version")
    parser.add_option("-r", "--test_route", dest="route_test", action="store_true",
                      help="Use option --test_route (or -r) to test the route line for input files using the gaussian utility, does not submit to queue (default False).", default=False)
    parser.add_option("-k", "--test_job", dest="test_job", action="store_true",
                      help="Use option --test_job (or -k) to quickly test gaussian input files using gaussian. Does not submit to queue (default False).", default=False)
    parser.add_option("-c", "--check_memory", dest="chk_mem", action="store_true",
                      help="Use option --check_memory (or -c) to quickly check the minimum memory requirement estimate for gaussian frequency calculations (memory is PER core). Does not submit to queue (default False).", default=False)
    parser.add_option("-n", "--nosub", dest="nosub", action="store_true",
                      help="Use option --nosub (or -n) to create submission files but don't submit to queue (default False). Alters the gaussian input files to reflect the processor and memory requested, using default 8-core/16GB settings if no -p/-m is provided.", default=False)
    parser.add_option("-x", "--exclusive", dest="exclusive", action="store_true",
                      help="Use option --exclusive (or -x) to reserve a whole node for the calculations, job will check the resources available on the node and use all of it by default. (default False).", default=False)
    # The following options are currently being tested, they may not work perfectly for all cases.
    parser.add_option("-V", "--Verbose", dest="verbose", action="store",
                      help="Enter a number, either 0, 1, 2, or 3 corresponding to the level of verbose job logging output you would like (default is 2).", choices=['0', '1', '2', '3'], default="2")
    parser.add_option("-f", "--follow_up", dest="follow", action="store", type="string",
                      help="Execute command or sript when the calculation finishes successfully. Note aliases will not be understood and some limitations may apply, use at your own risk!", default=0)
    parser.add_option("-s", "--storage COMING SOON", dest="storage", action="store_false",
                      help="Use option --storage (or -s) to turn off the use of group storage for saving checkpoint files. By default these files are saved to our group storage and read it from there if the calculation is set to read from a checkpoint file. Using this option will have the checkpoint saved to the current submission directory. (default True). Not available yet.", default=True)
    # MAYBE?!?: I might add an option to zip/archive the checkpoint file or checkpoint directory to save storage space.
    parser.add_option("-H", "--extra_help", dest="ext_help", action="store_true",
                      help="Use option --extra_help (or -H) to get much more detailed help for all of the options. (default False).", default=False)
    (options, args) = parser.parse_args()
    # extra help option needs to be above the check for number of arguments or else using only -H causes an error.
    if options.ext_help == True:
        print(bcolors.OKBLUE + "Gaussian job submission for Hoffman2 computing cluster and the SGE queuing system." + bcolors.ENDC)
        print("------------------------------------------------------------------")
        print(bcolors.HEADER +"Script usage:"+ bcolors.ENDC)
        print(bcolors.HEADER +"For a single input file: "+ bcolors.ENDC +"$ "+sys.argv[0]+" <input>.com/gjf ")
        print(bcolors.HEADER +"Or with a period for all input files in directory: "+ bcolors.ENDC +"$ "+sys.argv[0]+" *.com/gjf ")
        print(bcolors.HEADER +"Or multiple files separated by spaces: "+ bcolors.ENDC +"$ "+sys.argv[0]+" <input1>.com <input2>.com ...")
        print(bcolors.HEADER +"For testing purposes, use option --nosub to create submission files but don't submit to queue."+ bcolors.ENDC)
        print (extra_help)
        quit()
    # check number of arguments, gives an error if no arguments (input files) are supplied, apart from when -h, -H, or --version is used.
    if len(args) < 1:
        parser.error("Incorrect number of arguments! \n     Use option -h for usage help or -H for extra help.")
    # Get the filenames from the command line prompt
    #files = []
    files = args[0]
    # check if the files are gaussian input files, and if they are, check to see if they exist. Helpful to prevent submission of things that aren't meant to be submitted.
    if os.path.splitext(files)[1] not in [".com", ".gjf"]:
        print(bcolors.WARNING + "The file " + files + " does not appear to be an Gaussian input file?" + bcolors.ENDC)
        print("------------------------------------------------------------------")
        print(bcolors.HEADER +"Make sure you are in the right directory and that the files are Gaussian input files (.com or .gjf)."+ bcolors.ENDC)
    else:
        exists = os.path.isfile(files)
        if exists:
            pass
        else:
            print(bcolors.WARNING + "The file " + files + " does not appear to exist?" + bcolors.ENDC)
            print("------------------------------------------------------------------")
            print(bcolors.HEADER +"Make sure you are in the right directory and that the files are Gaussian input files (.com or .gjf)."+ bcolors.ENDC)
    if len(sys.argv) > 1:
       for elem in sys.argv[1:]:
          try:
             if os.path.splitext(elem)[1] in [".com", ".gjf"]:
                for filename in glob(elem):
                    if options.route_test == False and options.test_job == False and options.chk_mem == False:
                        print(bcolors.OKBLUE + "Preparing gaussian (" + options.gaussian_version + ") input file and submission script for job " + filename + "." + bcolors.ENDC)
                        # These lines are for fixing filename if it contains spaces or parentheses. (will fix this in the future)
                        # g_filename = g_filename.replace(' ', '_')
                        # g_filename = g_filename.replace('(', '_')
                        # g_filename = g_filename.replace(')', '_')
                        g_filename = os.path.splitext(filename)[0]
                        extension = os.path.splitext(filename)[1]
                        subname = g_filename+'.sh'
                        write_subfile(subname, g_filename, extension, options.gaussian_version, options.nproc, options.time, options.mem, options.exclusive, options.verbose, options.follow, options.nosub)
                        if options.nosub == False :
                            os.system('qsub '+ subname)
                            print(bcolors.OKGREEN + "Calculation " + g_filename + " has been submitted to the queue." + bcolors.ENDC)
                            if options.discard == True :
                                os.system("rm -f " + subname)
                                print(bcolors.OKBLUE + "Removed gaussian job submission file, " + subname + " " + bcolors.ENDC)
                        else:
                            print(bcolors.OKGREEN + "Submission file for " + g_filename + " created but not submitted." + bcolors.ENDC)
                            if options.discard == True :
                                os.system("rm -f " + subname)
                                print(bcolors.OKBLUE + "Removed gaussian job submission file, " + subname + " " + bcolors.ENDC)
                    if options.route_test == True:
                        g_filename = os.path.splitext(filename)[0]
                        test_route(filename)
                    if options.test_job == True or options.chk_mem == True:
                        g_filename = os.path.splitext(filename)[0]
                        extension = os.path.splitext(filename)[1]
                        test_job(g_filename, extension, options.chk_mem)
                    if os.path.isfile(filename) == None:
                        print(bcolors.WARNING + "The file does not appear to exist?" + bcolors.ENDC)
                    # else:
                        # May add something here in the future.
          # This except function doesn't seem to work properly, I think this needs python >3. Instead using "if len(args) < 1:" and parser.error (code is ~50 lines above) works as a replacement...
          except IndexError:
                print(bcolors.OKBLUE + "Gaussian job submission for Hoffman2 computing cluster and the SGE queuing system." + bcolors.ENDC)
                print("-------------------------------------------------")
                print(bcolors.HEADER +"Script usage:"+ bcolors.ENDC)
                print(bcolors.HEADER +"For a single input file: "+ bcolors.ENDC +"$ "+sys.argv[0]+" <input>.com/gjf ")
                print(bcolors.HEADER +"Or with a period for all input files in directory: "+ bcolors.ENDC +"$ "+sys.argv[0]+" *.com/gjf ")
                print(bcolors.HEADER +"Or multiple files separated by spaces: "+ bcolors.ENDC +"$ "+sys.argv[0]+" <input1>.com <input2>.com ...")
                quit()


if __name__ == "__main__":
    main()


##################################################################

# Notes specifically regarding the Hoffman2 computing cluster:
#
# Walltime is in hours, can be 1 to 336. If more than 24 hours the highp keyword is added (this is mandatory for the job to run).
#    with the highp option (>24 hours) the jobs are limited to only the 30 available Houk nodes, which may increase queue wait time.
#
# Nproc can be up to 36-cores(+ a few larger nodes), the more cores requested the potentially longer queue time.
#    Here is a summary of the nodes available on the hoffman2 cluster (as of Aug/2019):
#           144 nodes with 36 processors
#           12 nodes with 72 processors   (< unlikely gaussian jobs will need these)
#           9 nodes with 32 processors
#           136 nodes with 24 processors
#           236 nodes with 16 processors
#   ^ G16A03 can use most of the 16-core nodes in addition to all the nodes above(24-72core nodes)
#           341 nodes with 12 processors
#           460 nodes with 8 processors
#   ^ In addition to all nodes G16AO3 uses, G16A03SSE4 can use most of the 12-core nodes and ~half the 8 core nodes.
#
# Use of Exclusive requests a full node regardless of the number of processors,
#    this flexibility allows for shorter queue waiting times and more efficient use of resources.
# Once a job starts the submit script will find out how many processors and amount of memory
#    are available on the allocated node and then the input file is automatically updated making use of the
#    full node by using the recommended %cpu=#-# setting and changing the memory requested.
#  For exclusive G16A03 is limited to 16-core nodes and up. G16A03SSE4 can run on 8-core and up nodes.
#   By using exclusive the script will request a node with at-least 60GB of memory which covers every node
#    that G16AO3 can run on, if the node has more memory the job will of course make use of it.
#   If you want to make sure you get a node with more than 60GB of memory for certain jobs then simply
#     request it via the -m ##GB option in combination with -x (exclusive) option. Less than 60GB is ignored.
#
#  * Note: 4GB of ram per core is the recommended amount for gaussian jobs, but not all nodes have
#    4GB per core. Every node has at-least 2.5GB per core so using 2GB per core for the calculation
#    is the best compromise for between for shortest possible queue wait time and job performance.
#  Using at least 4GB per core is still recommended for larger jobs (50 atoms or 500 basis functions and up)
#    even though the jobs 'may' take longer to start.
#
# * No Houk node has more than 5.3GB per core, so never ask for more than 5.3GB per core with highp (job longer than 24 hours).
#   Keep in mind only 7 Houk nodes have more than 4GB per core (5.3GB max). Many Houk nodes have less than 4GB per core (13 out of 30)
#     so be considerate using highp (or more than 24 hours) for jobs that will take 4GB per job or greater.
#
#  * Using the highp keyword doesn't guarantee your job will start quicker. Due to normally high demand for Houk nodes,
#    it is likely a job will start sooner if not using highp and even if having to resubmit the job after 24 hours
#      your job may finish quicker overall rather than waiting for Houk nodes to become available.
#
# This script also handles moving checkpoint files to the node for the calculation,
#    and moving it back after the calculation. It will handle the use of %oldchk as well
#    to read from an old checkpoint but write to a new one.

##################################################################

# *** On-node scratch storage is called $TMPDIR on hoffman2
# Use $TMPDIR for job files when jobs are running and for high activity files to avoid unnecessary overhead of network traffic associated with the network file systems and improve you jobs performance.
#  Files in $TMPDIR will be deleted by the job scheduler at the end of your job or interactive session. If you want to keep files written to $TMPDIR, tell your program to copy them to permanent space before the end of your job or session. Files written to $TMPDIR are not backed up.

# *** $SCRATCH on hoffman2:
# The global scratch file system is mounted on all nodes for hoffman2 cluser. There is a 2TB per user limit. The system provides an environmental variable $SCRATCH which is a unique directory for your user files on the global scratch file system.
# Under normal circumstances, files you store in $SCRATCH are allowed to remain there for 14 days. Any files older than 14 days may be automatically deleted by the system to guarantee that enough space exists for the creation of new files.
# However, there may be occasions when even after all files older than 14 days have been deleted, there is still insufficient free space remaining. Under that circumstance, files belonging to those users who are using the preponderance of the disk space in $SCRATCH
#  will be deleted even though they have not been there for 14 days. Files written to $SCRATCH are not backed up.

##################################################################
