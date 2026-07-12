#!/bin/bash
#SBATCH -p gpu20 
#SBATCH -t 1:20:00
#SBATCH -o slurm-%j.out
#SBATCH --gres gpu:1
#SBATCH --array=1-10
#SBATCH -o      Models/slurm_log/slurm-%x-%j-%a.log
#SBATCH --error Models/slurm_log/slurm-%x-%j-%a.err
n_iter=9
numObject=10
# counter for jobs
cnt_job=1
for (( N = 1; N <= $numObject; N++ ))
do
	if [[ "$cnt_job" -eq "$SLURM_ARRAY_TASK_ID" ]];
	then
		python Forward_UANA_diverse_activation.py -net_n $N -iter_num $n_iter
	fi
	let "cnt_job++"
done
