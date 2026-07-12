#!/bin/bash
batch_num=2
iter_n=9
source /opt/openfoam5/etc/bashrc
cd /home/airfoil_UANA
echo "Running new data set generation..."
python3 new_dset.py -n_batch $batch_num -iter_num $iter_n
echo "Python script finished."
