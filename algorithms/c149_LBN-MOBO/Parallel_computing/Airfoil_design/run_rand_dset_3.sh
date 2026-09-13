#!/bin/bash
batch_num=3
source /opt/openfoam5/etc/bashrc
cd /home/airfoil_UANA
echo "Running Python script..."
python3 Random_dataset_gen.py -n_batch $batch_num
echo "Python script finished."
