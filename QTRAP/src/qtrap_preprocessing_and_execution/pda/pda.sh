#!/usr/bin/env bash
#$ -cwd
#$ -l h_data=1571.5M,h_rt=24:00:00,arch=intel-gold*
#$ -pe shared* 12
#$ -j y
#$ -o joblog.pda.$JOB_ID
#$ -M $USER@mail
#$ -m bea

# qsub script for MMPBSA partial decomposition analysis.
#
# Placeholders are replaced by queue_pda_jobs.sh:
#   xx = imaged trajectory prefix
#   xy = solvated topology file
#
# Inputs:
#   decomp.in
#   imaged trajectory .nc file
#   complex, receptor, ligand, and solvated topology files
#
# Outputs:
#   FINAL_RESULTS_MMPBSA.dat
#   FINAL_DECOMP_MMPBSA.dat
#   other default output files for this job type

module load amber/amber20

MMPBSA.py -O \
    -i decomp.in \
    -cp complex-bondi.parm7 \
    -sp xy \
    -rp enzyme-bondi.parm7 \
    -lp ligand-bondi.parm7 \
    -y xx.nc \
    -o FINAL_RESULTS_MMPBSA.dat \
    -do FINAL_DECOMP_MMPBSA.dat
