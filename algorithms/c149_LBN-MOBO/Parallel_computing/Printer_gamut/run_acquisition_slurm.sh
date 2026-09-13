#!/bin/bash
cd /HPS/NavidCAM/work/NAGD/MO-NBO/AB/40_ink_automized_not_random_slurm
conda activate mina
sbatch Acquisition.sh
squeue -u nansari