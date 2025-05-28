#!/bin/bash

#SBATCH --job-name=optuna-db
#SBATCH --time 4-00:00

#SBATCH --ntasks 1
#SBATCH --cpus-per-task 4

#SBATCH -o "db_%j.log"

echo "Started at $(date --rfc-3339=seconds)."
echo "Host: $(hostname)"
echo "Main Job ID: $SLURM_ARRAY_JOB_ID"
echo "Job ID: $SLURM_JOB_ID"

# port="${SLURM_STEP_RESV_PORTS}"
# if [ -z "$port" ]; then
#     echo "ERROR no port assigned"
#     exit 2
# fi

user=default
pass=8blSAXk6KRZ089m7
port=6379
host="$(hostname -s)"

echo "Redis URL: redis://${user}:${pass}@${host}:${port}"
echo "Server starting..."

"$HOME/lebeau_shared/.local/bin/redis-server" redis.conf --port "$port" --requirepass "$pass"
