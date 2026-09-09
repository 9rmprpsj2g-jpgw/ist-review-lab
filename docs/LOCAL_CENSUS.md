# Run the approved census on macOS

> **Historical attempt — abandoned before either gate passed (user report, 2026-09-08).** The Intel Mac has 8.0 GiB total RAM, not the 14 GB the user previously supplied. A clean conda environment installed every exact pin and passed `pip check`; `prepare_local_data.py` verified both immutable source and reference-audit digests. After other applications were closed, available RAM was only 0.92–1.02 GiB and swap declined from 2.83 to 0.6 GiB. Both `preflight_local.py` and `check_local_storage.py` stopped at the unchanged 4 GiB available-memory requirement. Storage trials did not start; neither gate passed; **no census ran**. The user attributed roughly 7 GiB to macOS/background services. The prior worker sizing and threshold were based on the user's erroneous memory figure. No single-worker or reduced-memory Mac alternative is authorized. The instructions below are retained as the attempt record; use [LINUX_CENSUS.md](LINUX_CENSUS.md) for the active handoff.

Patch base: **cbe42024cc632bc1872f18a7ed45313944e48361**. This preparation runs no census in the sandbox. The local job is 5 topics × 3 seeds × 12 policies = 180 runs, each at 23,149 documents, with two workers. Production max_iter is 41,000. No Phase 4 analysis is included.

Download `local-census-from-cbe4202.patch` and `local-census-inputs.zip` into `~/Downloads`. The ZIP contains the exact source corpus and an existing full-size audit used only to test storage; it does not supply any new-generation outcomes. The installer checks their unchanged committed digests before publishing them. The raw corpus is only 3,853,819 bytes; the storage reference is 87,782,855 bytes uncompressed. Neither belongs in Git.

## Commands, in order

Run each command only after the previous command succeeds. The example creates a new checkout so it cannot collide with your existing working tree. If using your existing checkout, replace the first three commands with `cd` into it and confirm its HEAD and clean status match the base before applying anything.

```bash
git clone https://github.com/9rmprpsj2g-jpgw/ist-review-lab.git ist-review-lab-local
cd ist-review-lab-local
git switch -c local-census cbe42024cc632bc1872f18a7ed45313944e48361
git rev-parse HEAD
git status --short
git apply --check "$HOME/Downloads/local-census-from-cbe4202.patch"
git apply "$HOME/Downloads/local-census-from-cbe4202.patch"
git add -A
git commit -m "Prepare local census: iteration budget, convergence records and verified resume"

conda create --name ist-review-census --override-channels -c conda-forge python=3.12.13 pip -y
conda activate ist-review-census
python --version
python -m pip install --only-binary=:all: -r requirements-census.txt
python -m pip check

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export PYTHONUNBUFFERED=1

python scripts/prepare_local_data.py "$HOME/Downloads/local-census-inputs.zip"
python scripts/preflight_local.py --generation census-v2-local
python scripts/check_local_storage.py --generation census-v2-local
python -u scripts/local_census.py --generation census-v2-local
python scripts/verify_audits.py audit_manifests/census-v2-local.json
```

The filesystem check is a separate gate. Do not start the next command if it fails. Non-convergence during production is recorded and review continues; exit code 2 at the end means the complete data include non-converged fits and require review. No code automatically increases max_iter. A worker exception, missing completed file or digest mismatch is a hard stop, not a request to retry.

## Anaconda, Python and hardware assumptions

Anaconda itself is not the problem; reusing its base environment would import uncontrolled package versions and native libraries. Use the new dedicated environment above, with the exact pinned pip wheels. Do not install these packages in `base`, mix in previously installed scientific packages or substitute a different Python version to make the preflight pass. Conda recommends isolating environments when combining conda and pip: [Conda environment guidance](https://docs.conda.io/activation).

I cannot verify your Mac's CPU architecture, macOS release, conda-forge availability for CPython 3.12.13 or whether every pinned wheel is available for your platform. If environment creation or wheel installation fails, stop and provide that output. Do not replace a pin silently. CPython 3.12.13 is source-only on python.org, so there is no official 3.12.13 macOS installer to point you to: [Python 3.12.13 release](https://www.python.org/downloads/release/python-31213/). A separate uv-managed CPython 3.12.13 is an alternative if conda cannot supply it; uv documents exact-version installation at [uv Python installation](https://docs.astral.sh/uv/guides/install-python/).

Your stated 14 GB of memory should be sufficient relative to the sandbox's approximately 2.29 GiB two-worker estimate, but that is not a native Mac measurement or an upper bound. Preflight requires at least **4 GiB currently available RAM** and **20 GiB free disk** at the audit/output/manifest locations for a fresh generation. Subsequent launches credit that generation’s existing files against the initial 20 GiB allowance, with a minimum 2 GiB free reserve, so completed work does not itself block resume. These are operational reserves, not measured scientific constants. The storage check reports native per-trial peak RSS and wall time; the census reports native worker high-water RSS and sampled aggregate process-tree RSS. Keep the machine on power, awake and the terminal open. CPU speed and native libraries may change elapsed time; the earlier under-seven-hour estimate is not a Mac runtime promise.

The single-thread environment settings avoid native thread oversubscription inside the two workers; they do not change C, loss, dual, tolerance or sampling. See scikit-learn's explanation: [scikit-learn parallelism documentation](https://scikit-learn.org/stable/computing/parallelism.html). Native macOS/ARM/x86 and library-build differences may change floating-point behavior. The runner records the local feature fingerprint and binds workers/resume to it. It does not assert bitwise equivalence with Linux or update any historical expected fingerprint to make a mismatch pass.

## What the preflight and filesystem check do

Preflight performs no fit. It checks the exact Python implementation/version, all entries in `requirements-census.txt`, a clean committed checkout descended from the confirmed base, source-lock identity, corpus and reference-audit digests, thread limits, free space, available RAM, and immutable topic N/R counts. It builds the feature matrix to record its local fingerprint. No collection download or source-lock regeneration is allowed to conceal missing inputs.

`check_local_storage.py` runs the six unchanged Phase 3C write contracts with temporary files on the audit volume. It then performs twenty independent full-size audit writes there, serially, with the real matrix resident and strict decoded-value verification. Each child exits completely before the parent reparses and compares the final bytes to the committed reference digest. There are no retries. Failed temporary/final files are preserved where captured; logs are under `local_outputs/census-v2-local/storage-check-*/`. Successful trial files remain under the corresponding `audit_store` directory. Zero observed failures in this finite check is not proof that storage can never fail; all census publication checks stay enabled.

## Progress, interruption and resume

The runner prints START, PROGRESS about every ten seconds of review work, FINISHED and COMPLETE n/180 messages. Serialization/verification can take additional seconds after the last review update. FIT_WARNING lines name policy, seed and fit; the surrounding run prefix identifies the topic. Each worker has a durably published full stdout/stderr log under `audit_store/census-v2-local/logs/`, including unique attempt identifiers. The manifest retains parent exceptions and resource/session summaries. Per-fit warnings remain in every audit even if terminal output is lost.

To resume after Ctrl-C or a lost parent process, activate the same environment, repeat the five export commands above, and run:

```bash
python -u scripts/local_census.py --generation census-v2-local
```

Do not rerun the filesystem check or change the generation name just to resume. Keep the same code commit, dependencies, configuration, paths and environment. A code/configuration/environment change requires a distinct generation and new preflight/storage check; it is not an exact continuation. The current generated manifest is the only permitted worktree change during resume; source edits and other untracked files still stop preflight. Keep manifests uncommitted until generation completion, because committing during a generation changes the recorded code-commit identity.

Resume checks every completed audit and producer receipt against the prior manifest, including original digests, resolved parameters, row-order replay, candidate/margin completeness, topic prevalence and convergence metadata. Valid completed runs are skipped. An interrupted trajectory restarts at its seed; there is no within-fit or within-run checkpoint. A completed audit without a producer receipt cannot be certified from a newly computed digest: if structurally valid it is preserved in `uncommitted/` and that run restarts. A receipt missing its audit, an invalid audit or a changed previously completed entry stops. Prior FAILED generations require review; there is no automatic error retry. Generation locks and parent-death handling prevent concurrent old/new workers from publishing into the same generation.

## Outputs and completion

- `audit_store/census-v2-local/*.json`: all 180 audits, ignored by Git.
- `audit_store/census-v2-local/receipts/`: producer completion receipts, ignored.
- `audit_store/census-v2-local/logs/`: full per-worker logs, ignored.
- `local_outputs/census-v2-local/`: preflight, storage gate, resolved config, actual model parameters and per-run table, ignored.
- `audit_manifests/census-v2-local.json`: generation identity, expected grid, byte sizes, digests, completeness, per-policy/per-topic non-convergence counts including zeros, timing, RSS and source/code/environment provenance. Commit this manifest after completion; keep the raw audits durably on your machine with a backup.

`COMPLETE` requires all 180 validated run/receipt pairs. `COMPLETE_WITH_NONCONVERGENCE` preserves all data but requires review; it is not a fully converged result. The standalone verifier checks transferred/retained audits against that manifest. Report the manifest, logs, non-convergence counts, actual audit sizes and resources before authorizing Phase 4. The 38 audits from the earlier failed generation are superseded for production and never reused here.

## Verification performed for this handoff

The nine authorized high-ceiling refits completed in the sandbox, with immutable-input checks and independent post-exit state verification. All 28 contract tests passed, including the twenty existing tests unchanged and eight new mocked orchestration/convergence contracts. No macOS installation, full-size Mac filesystem check, or actual census was executed here. macOS execution is a user-side gate, not a completed validation claim.
