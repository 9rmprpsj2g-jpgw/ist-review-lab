#!/bin/bash
# ADJUST RESOURCE REQUESTS HERE (or override with sbatch command-line options).
#SBATCH --job-name=ist-census
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
# Add --account, --partition, --constraint or --nodelist via sbatch as your site requires.
# END ADJUSTABLE RESOURCE REQUESTS. Preserve termination signal and no-requeue policy.
#SBATCH --signal=B:USR1@300
#SBATCH --no-requeue
#SBATCH --output=local_outputs/slurm-%j.log
#SBATCH --open-mode=append

set -euo pipefail
: "${CENSUS_PYTHON:?Export the absolute pinned environment Python path before sbatch}"
: "${CENSUS_GENERATION:?Export one generation ID, retained across resumes}"
cd "${SLURM_SUBMIT_DIR:?Submit from the checkout root on persistent storage}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
export PYTHONHASHSEED=0

# This shell is the only recipient of the advance warning. Forward it to the
# coordinator, which handles INTERRUPTED and terminates/waits for its workers.
# Gates run before any fit. A failed gate exits; it is never retried here.
active_pid=''
stop_job() {
    trap '' USR1 TERM
    if [[ -n "$active_pid" ]]; then
        kill -TERM "$active_pid" 2>/dev/null || true
        wait "$active_pid" || true
    fi
    exit 143
}
trap stop_job USR1 TERM

"$CENSUS_PYTHON" -u scripts/linux_census.py gates --generation "$CENSUS_GENERATION" &
active_pid=$!
wait "$active_pid"
active_pid=''
"$CENSUS_PYTHON" -u scripts/linux_census.py run --generation "$CENSUS_GENERATION" &
active_pid=$!
wait "$active_pid"
active_pid=''
"$CENSUS_PYTHON" scripts/verify_audits.py \
    "audit_manifests/$CENSUS_GENERATION.json"