#!/bin/bash
#SBATCH -p gpu20 
#SBATCH -t 05:00
#SBATCH -o slurm-%j.out
#SBATCH --gres gpu:1
#SBATCH --array=1-20
#SBATCH -o      Acquisition/slurm_log/slurm-%x-%j-%a.log
#SBATCH --error Acquisition/slurm_log/slurm-%x-%j-%a.err
n_iter=9
numObject=20
# counter for jobs
cnt_job=1
for (( N = 1; N <= $numObject; N++ ))
do
	if [[ "$cnt_job" -eq "$SLURM_ARRAY_TASK_ID" ]];
	then
		python Acquisition_4_D.py -run_n $N -iter_num $n_iter
	fi
	let "cnt_job++"
done
