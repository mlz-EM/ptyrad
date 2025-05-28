#!/bin/bash

# slurm parameters. See sbatch documentation online
#SBATCH --job-name "ptyrad"

# request half node
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 20

# request GPU node
#SBATCH --constraint=xeon-g6
#SBATCH --gres=gpu:volta:1

# log filename
#SBATCH --array 0-7%8
#SBATCH -o "run_%a.log"

echo "Started at $(date --rfc-3339=seconds)."
echo "Host: $(hostname)"
echo "Main Job ID: $SLURM_ARRAY_JOB_ID"
echo "Job ID: $SLURM_JOB_ID"
echo "Array Index: $SLURM_ARRAY_TASK_ID"

# load cuda libraries
module unload cuda
module load cuda/11.8
module unload anaconda
eval "$(conda 'shell.bash' hook)"

conda activate ptyrad

ptyrad run --params_path "PZT_reconstruct.yml" --gpuid 0
