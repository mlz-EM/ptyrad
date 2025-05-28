# Running PtyRad Optimizer with Optuna and Redis Storage

Follow the steps below to run the PtyRad optimizer using Optuna with Redis-based storage on an HPC environment. Example files are locacled in [https://github.com/mlz-EM/ptyrad/blob/main/configs/reconstruct.yml](https://github.com/mlz-EM/ptyrad/tree/mlz/demo/mlz_optimizer). [A few lines of code](https://github.com/mlz-EM/ptyrad/blob/ac078b13a1ba2174d055108c9c86262ecf7502a3/src/ptyrad/reconstruction.py#L157-L161) are changed.


## Steps

1. **Launch Redis Server on HPC**
   - Submit the Redis server script to the HPC job scheduler:
     ```bash
     sbatch redis-server.sh
     ```
   - This will host a Redis server instance on one of the compute nodes.

2. **Configure Redis Storage Path**
   - After the Redis server starts, locate the Redis URL in the `db*.log` file.
   - Replace the `storage` field in the `reconstruct.yml` configuration file with this Redis URL.  
     Example:
     ```yaml
     storage: redis://default:<password>@<host>:6379
     ```

3. **Launch PtyRad Optimization Job Array**
   - Submit the PtyRad optimization script:
     ```bash
     sbatch ptyrad_redis_opt.sh
     ```
   - This will create a job array to run the optimization in parallel.

4. **Establish SSH Tunnel from Local Machine**
   - On your local machine, set up port forwarding to connect to the Redis server:
     ```bash
     ssh -L 6379:d-6-1-2:6379 supercloud
     ```
   - Replace `d-6-1-2` with the actual node name where Redis is hosted (as found in `db*.log`).

5. **Launch Optuna Dashboard Locally**
   - Open another terminal and activate the environment where Optuna is installed.
   - Run the Optuna dashboard:
     ```bash
     optuna-dashboard redis://default:<password>@localhost:6379
     ```
   - Replace the URL with the one found in `db*.log`.

6. **Access the Dashboard in Browser**
   - In your web browser, go to:
     ```
     http://localhost:8080/
     ```

---

**Note:** Ensure that all firewall settings and SSH permissions are properly configured to allow tunneling and dashboard access.
