# Linux census handoff — preparation, not an executed census

Confirmed checkout and future patch base: **48c9ca1b52b26c93ed31ec17ca303e1246583be9** on `local-census`. The Linux handoff was transferred as complete files, verified locally, and committed directly. The corrupt patch was never applied. Clone and check out this commit using the commands below. No census ran on the Mac, and no census is authorized in this sandbox. The macOS attempt is retained in [LOCAL_CENSUS.md](LOCAL_CENSUS.md).

## Machine to request

| Target | RAM | CPU | Persistent SSD | Workers |
|---|---:|---:|---:|---:|
| Recommended VM | 32 GB | 4 x86_64 vCPU | 100 GB | 2 |
| Minimum practical dedicated VM | 16 GB | 2 x86_64 vCPU | 50 GB | 2 |
| Slurm allocation on a larger node | 16 GiB requested per node | 1 task, 4 CPUs | at least 20 GiB free and sufficient quota | 2 |

The proposed Ubuntu 22.04 or 24.04 LTS VM is comfortably sized; its RAM/disk exceed the practical minimum and provide useful operating-system, cache and retained-evidence headroom. A GPU is unnecessary. Request a dedicated or sustained-performance CPU instance, not one dependent on burst credits. These are engineering sizing recommendations, not measurements on the new host. Keep two workers even on 32 GB; four-worker concurrency has not been benchmarked. A smaller dedicated machine might fit the measured process footprint, but it is not the recommended minimum. This is no proposal to rehabilitate the 8 GB Mac.

Unchanged gates: **4 GiB currently available RAM**, **20 GiB initial free disk** with the existing resume credit and 2 GiB reserve, CPython **3.12.13**, every package pin, immutable source/reference digests, six Phase 3C contracts and **20 full-size write/verify trials**, then full per-run production verification. Linux additionally checks memory controller limits/usage, so host-wide available RAM cannot stand in for an exhausted Slurm allocation. It stops if a Slurm memory controller/cap cannot be read; ask the site administrator rather than bypassing this check. The kernel documents current usage and hierarchical limits in its [cgroup memory documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html).

**Wall time is an estimate:** provision a **12-hour first allocation**. The prior model-work estimate was under seven hours on the sandbox CPU, not a timing guarantee for a VM or cluster. Allow roughly **8–12 hours of reservation** for the first attempt, including setup/gates, full verification, worker startup and storage overhead. On slower/shared CPUs or network filesystems it can take longer. This is a scheduling allowance, not an observed runtime range. The two-worker approximately 2.29 GiB estimate and single verification peak of approximately 889 MiB were sandbox observations/arithmetic, not bounds on a new host. Audit storage remains approximately 4.4 GB estimated, plus receipts, logs, reference trials (about 1.64 GiB per gate), retained failures and backups. The new run records actual time/RSS/bytes.

## Filesystem decision before installation or gates

Prefer a persistent ext4 or XFS filesystem on an attached SSD/block volume. A remote-backed block volume is not the same thing as a network-mounted filesystem; neither the word “cloud” nor “scratch” establishes correctness. Do not use Docker overlay, a notebook container writable layer, tmpfs, or a job-local disk that disappears at allocation end. This handoff rejects overlay/aufs and memory-backed mounts; it does not certify other filesystem types by name.

Choose one persistent directory for the **whole checkout**, including `data/`, `audit_store/`, `local_outputs/` and `audit_manifests/`. Keep them on the same filesystem; the Linux preflight enforces this. On a VM, an attached volume mounted at `/data` is suitable after the provider has provisioned/formatted/mounted it. Do not run formatting commands against an unidentified device. On a cluster, ask for a persistent project/scratch allocation whose retention exceeds the run and review period.

Inspect the actual paths, not just `/`:

```bash
findmnt -T /data -o TARGET,SOURCE,FSTYPE,OPTIONS
df -h /data
df -i /data
# After cloning, from the checkout root:
findmnt -T . -o TARGET,SOURCE,FSTYPE,OPTIONS
findmnt -T audit_manifests -o TARGET,SOURCE,FSTYPE,OPTIONS
```

`findmnt --target` identifies the mount serving a path; it does not prove durability. See [findmnt documentation](https://man7.org/linux/man-pages/man8/findmnt.8.html). Confirm read/write access, available bytes AND inode/quota headroom, persistence across reboot/job exit, cleanup policy, and whether the site supports fsync, directory fsync, same-directory atomic rename, hardlinks and advisory locks. Ask the administrator about filesystem errors and quotas (`df` is not a quota check). The unchanged write contracts exercise the writer; obtain site confirmation that advisory locking works if other jobs could access the generation.

**Where to run the check:** on the filesystem actually receiving all run artifacts, from the compute node/allocation that will run the census. The command stages the full audit under that checkout's actual `audit_store/<generation>/` path. A test on `$HOME` does not qualify scratch; a scratch test does not qualify `$HOME`. With the supported single-filesystem layout, the audit test also exercises the filesystem containing the working directory and logs. If considering two candidate volumes, place a separate clean checkout and the reference inputs on each and run `preflight` and `storage` there, with separate generation IDs; neither receipt authorizes the other. Do not split one generation's output directories across mounts.

For a second backup/transfer destination, verify the copied audits against the original generation manifest after copying. If it will become an active run destination, it needs its own full-size gate; do not move an in-progress generation and call it a resume. Neither 20 successful trials nor a checksum proves indefinite storage reliability. Staged and final full-value checks, independent post-exit digests and record counts stay enabled throughout production. Any failure preserves evidence and stops; no retry, threshold reduction, streaming or chunking workaround is introduced.

## VM setup, commands in order

Use an ordinary SSH account with sudo. On Ubuntu, install command-line prerequisites (skip apt on university systems):

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates util-linux tmux
```

Put the already supplied **unchanged** `local-census-inputs.zip` in `$HOME/Downloads` on this Linux host (SCP/SFTP is sufficient). The code is already committed; no patch download or application is needed. Ask the provider to mount the persistent volume at `/data` and grant your account write access there. If the VM's persistent root disk has the space, use a directory in your home instead and substitute that parent consistently. Then:

```bash
cd /data
git clone https://github.com/9rmprpsj2g-jpgw/ist-review-lab.git
cd ist-review-lab
git switch --detach 48c9ca1b52b26c93ed31ec17ca303e1246583be9
git rev-parse HEAD
git status --short
```

HEAD must be `48c9ca1b52b26c93ed31ec17ca303e1246583be9`, and `git status --short` must produce no output. This commit contains the verified Linux handoff; its older documentation still mentions the unused patch, so follow the corrected instructions here. Do not start a generation with uncommitted preparation edits; do not change commits or commit again until that generation is complete.

Use a new Linux environment; do not copy the Intel Mac's installed wheels/environment. If conda already exists, skip its installation and create the environment below. Otherwise the following user-local Miniforge installation needs no root. Miniforge supplies conda; the project's environment version is independent of its installer/base Python. Verify the installer against the release's checksum, and stop on mismatch. See [official Miniforge installation instructions](https://github.com/conda-forge/miniforge).

```bash
mkdir -p "$HOME/Downloads"
cd "$HOME/Downloads"
curl -fLO https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
curl -fLO https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh.sha256
sha256sum -c Miniforge3-Linux-x86_64.sh.sha256
bash Miniforge3-Linux-x86_64.sh -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda create --name ist-review-census --override-channels -c conda-forge python=3.12.13 pip -y
conda activate ist-review-census
cd /data/ist-review-lab
python --version
python -m pip install --only-binary=:all: -r requirements-census.txt
python -m pip check
```

The existing requirements file is reused byte-for-byte; its historical “macOS wheels required” comment describes the previous attempt. On Linux pip resolves Linux wheels at those exact versions. Wheel availability and the site's package-network access have not been tested here. Stop rather than substituting a Python/package version. Do not use the system Python or install into Anaconda base.

Start `tmux new -s ist-census` before the gates/run so an SSH disconnect does not terminate them. Activate the same environment inside tmux, then run each command only after the previous one succeeds:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
export PYTHONHASHSEED=0
python scripts/prepare_local_data.py "$HOME/Downloads/local-census-inputs.zip"
python scripts/capture_command.py local_outputs/linux-contracts.log python -m unittest discover -s tests -v
python -u scripts/linux_census.py preflight --generation census-v2-linux
python -u scripts/linux_census.py storage --generation census-v2-linux
python -u scripts/linux_census.py run --generation census-v2-linux
python scripts/verify_audits.py audit_manifests/census-v2-linux.json
```

The standalone `storage` command runs the same six Phase 3C contracts and twenty full-size trials; **no fits**. It retains every reference trial plus durable child logs and a PASS/FAIL receipt. It must pass before `run`. It is not rerun to hide a failed trial. Native Linux RSS is converted from KiB correctly; Mac units remain bytes as before. Numerical logic, max_iter=41,000, convergence/warning logging, full publication verification and all existing assertions are unchanged.

## University computing without root

Use either of these environment routes; neither assumes both modules and conda:

1. **Conda available or user-local installation allowed:** create the same dedicated environment as above. A module-provided conda can also supply the command; use the site's documented module name, then create the environment. No apt/sudo needed.
2. **Modules only:** `module avail python`, then load the site's module that provides **CPython 3.12.13**, verify `python3 --version`, and run `python3 -m venv "$HOME/venvs/ist-review-census"`. Activate it with `source "$HOME/venvs/ist-review-census/bin/activate"`, install the unchanged requirements with `--only-binary=:all:`, and run `python -m pip check`. Module names are site-specific and cannot be supplied honestly before seeing the catalog. If no exact Python exists, request it from the administrator or use the user-local conda route if permitted; no silent pin change.

Install on a login node only if site policy allows package installation; all storage stress tests and model fits belong inside a compute allocation. Keep the same module environment and absolute Python path across jobs. If compute nodes have no internet, finish package/input installation before submitting; the run itself needs no network. This handoff requires Linux x86_64, Bash, git, findmnt, readable cgroup memory limits, and a compatible filesystem. Site-specific modules, quotas, partitions/accounts and library availability are unresolved assumptions.

From the prepared, committed checkout on persistent storage, with the pinned environment active and inputs installed:

```bash
mkdir -p local_outputs
export CENSUS_PYTHON="$(python -c 'import sys; print(sys.executable)')"
export CENSUS_GENERATION=census-v2-linux
sbatch scripts/census.slurm
```

The script clearly marks `--nodes=1`, `--ntasks=1`, `--cpus-per-task=4`, `--mem=16G` and `--time=12:00:00`. Use command-line overrides for the site account/partition/time/node so preparation source stays committed and unchanged, for example `sbatch --account=YOUR_ACCOUNT --partition=YOUR_PARTITION scripts/census.slurm` with actual site values. Four CPUs are allocated to **one coordinator with two subprocess workers**, not four independent census jobs. A 32 GiB memory request is acceptable if the site allocates whole nodes; it does not increase worker count. Slurm's per-node memory and CPU option semantics are documented in [sbatch](https://slurm.schedmd.com/sbatch.html).

The batch script runs `gates` before `run`. A first allocation runs both gates; subsequent allocations validate existing PASS receipts and identity without replacing them. Failed or unfinished storage evidence requires review, not an automatic retry. Watch `tail -f local_outputs/slurm-JOBID.log`; the script also retains normal durable per-worker logs and gate logs. Slurm itself writes its scheduler log outside the application helper; retain it as external operational evidence, not a durable completion receipt.

## Wall-clock termination and resume

The Slurm script requests an advance USR1 signal to its batch shell five minutes before the time limit. The shell forwards TERM to the Python coordinator; the Linux adapter enters the existing interruption cleanup, stops workers, waits, and publishes `INTERRUPTED`. Slurm can later kill remaining processes at its site-configured deadline, so cleanup is best-effort. The early-signal/termination behavior is described in [sbatch's signal and time options](https://slurm.schedmd.com/sbatch.html). No automatic requeue or integrity-failure retry is enabled.

After a time limit or operator interruption, inspect the scheduler and worker logs first. Confirm the previous job and workers have exited, preserve the generation ID, and resubmit the same script. On a VM, re-activate the same environment, export the same thread settings and run `python -u scripts/linux_census.py run --generation census-v2-linux`. Completed audit/producer-receipt pairs are fully revalidated and skipped. Interrupted trajectories restart from their seeds; there is no within-fit checkpoint. A hard kill may leave a RUNNING manifest; the same recovery validates pairs against the prior manifest before proceeding. Partial/invalid final artifacts or a FAILED status remain hard stops; do not delete them to force a resume.

**Strict resume limitation:** code commit, config, package versions, Python executable path, native platform/kernel identity and filesystem identity must still match. The Linux adapter additionally records/binds mount paths, sources, types and options. Cluster job IDs and hostnames are recorded as observations, not equality requirements, but a different node/kernel or differently mounted scratch may fail the existing identity checks. Prefer a homogeneous partition and the same persistent absolute checkout/environment paths; if necessary request the original node with `sbatch --nodelist=ACTUAL_NODE scripts/census.slurm`. If identity still differs, stop for review. This handoff does not waive a provenance check to make cross-node resume work. Node-local scratch deleted between jobs cannot support this resume contract.

## Retention and completion gate

Keep the VM/volume or cluster allocation's persistent storage until evidence is backed up and independently verified. Retain `audit_store/<generation>/` including producer receipts, worker logs and failed stages, `local_outputs/<generation>/`, scheduler logs and `audit_manifests/<generation>.json`. The raw audits stay ignored by Git. Use SCP/SFTP/rsync to obtain them separately; these transport utilities are not substitutes for the destination digest/parse checks. Preserve directory layout and run `python scripts/verify_audits.py audit_manifests/census-v2-linux.json` on the copied checkout after transfer. Commit the completed manifest only after the generation ends.

Completion requires all 180 untruncated audited runs, actual elapsed time/RSS/byte totals, non-converged fit counts by policy/topic including zeros, and inspection of all logs/captured warnings. `COMPLETE_WITH_NONCONVERGENCE` exits 2 with data retained and requires review; it is not permission to raise max_iter or proceed to analysis. Nothing here begins Phase 4.

## What has actually been validated

The original preparation gate passed **35 tests**, including the 28 existing tests unchanged. Its complete captured log contains only two deliberately injected convergence warnings from the existing mocked test. All 149 protected files compared with the preparation base `95cafe313c1861b41004cd5cfbc1c72fd2750c40` were unchanged. Bash/Python syntax checks passed. That historical evidence remains in `diagnostics/linux_handoff/`. The user subsequently verified all 13 transferred files, reported 35 tests passing locally, and committed the handoff as `48c9ca1b52b26c93ed31ec17ca303e1246583be9`. These checks do not constitute a census. No VM was provisioned, no native cloud/cluster package installation or full-size storage trial ran, and no Slurm scheduler was available here. Native gate receipts and the census completion evidence remain outstanding on the selected Linux host.