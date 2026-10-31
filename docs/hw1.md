# HW1 evidence

## Final local fresh-clone verification

On October 15, commit `42034e7` was cloned from this local repository
into a new directory with no DVC cache or restored data. Only the ignored
`.env` was copied for access to the existing local Silo service:

```powershell
# From the source checkout:
$cloneRoot = Join-Path $env:TEMP 'hw1-registry-check-lf-20261015'
git clone --local --no-hardlinks . $cloneRoot
Copy-Item .env (Join-Path $cloneRoot '.env')
Set-Location $cloneRoot
uv sync --all-groups
# Load AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as documented below.
uv run dvc pull
uv run dvc repro
uv run dvc repro
uv run dvc metrics show
Get-FileHash data/hour.csv -Algorithm MD5
```

```text
dvc pull: 5 files fetched and 5 files added
Both dvc repro invocations:
  Stage 'prepare' didn't change, skipping
  Stage 'train' didn't change, skipping
  Stage 'evaluate' didn't change, skipping
  Data and pipelines are up to date.
metrics/metrics.json: mae=46.27602, r2=0.89381, rmse=71.59137
Dataset MD5: BCBDBA906E4A9964CFAFED8B14549A62
git status --short: no changes
```

I ran `docker compose stop` to stop the services, then ran `uv run pytest -q` in the fresh clone and got `11 passed in 4.66s`. I started the services up again afterwards.

The first run on the final clone showed an unnecessary reevaluation was happening: it seems Python writes the metrics file with CRLF on Windows, while Git checked it out with LF. Now the metrics writer explicitly writes UTF-8 with LF, and the repeated run above shows that the outputs are byte-identical. The final verification commit changes only this evidence; the validated code and the state of the pipeline remain unchanged.

This set of runs uses the existing local Silo and MLflow storage. It doesn't check for access from another machine with clean Docker volumes. Grading access and repository submission are pending; no Git push was run.

## Four-setting comparison and registry (R7–R9)

All four configurations use the same version-two dataset, split on 2012-07-01 into 13,003 earlier training rows and 4,376 later evaluation rows, with random seed 42. RMSE in rentals/hour is the main selection metric since it penalizes large errors in demand. The results from the MLflow server on localhost are:

| Trees | Maximum depth | Minimum leaf size | Run ID | RMSE | MAE | R² |
| --- | --- | --- | --- | --- | --- | --- |
| 50 | 12 | 2 | 8fa1c3602eab4a1d875ad616490b68af | 73.56925 | 47.82911 | 0.887859 |
| 60 | 12 | 2 | b6e7eb51f67747c0991cf0f0f74a9053 | 73.58144 | 47.85641 | 0.887822 |
| **100** | **16** | **1** | **5907a49e09d24f678c8fb0ed265786c8** | **71.59137** | **46.27602** | **0.893808** |
| 100 | 8 | 4 | 2823b459ab054a628cff67e003b844ac | 89.81294 | 60.03313 | 0.832872 |

The model with depth 16 has the lowest RMSE as well as the lowest MAE. Increasing the original model from 50 to 60 trees made no difference, and the error for the shallower forest was much higher. However, this comparison is not exhaustive and does not identify a global optimum. Because the models were selected based on their performance in this time period, this score is really the selection period score, not a test period evaluation. The deployment metric should be evaluated on yet another, future period, or a rolling temporal assessment. Furthermore, since weather covariates are observed and used in the model, this is conditional hourly demand estimation, not a demonstrated advance weather forecast.

The winning parameters are set in `params.yaml` and recorded in `dvc.lock` as well as in the local metrics. The DVC command restored the matching cached outputs and did not run another training process, which would have resulted in duplicate model outputs. The full data-hash query results are saved as [`runs-for-data.json`](runs-for-data.json), including the duplicate earlier run with 50 trees from the console-encoding experiment.

```powershell
uv run python -m mlops_project.registry runs-for-data bcbdba906e4a9964cfafed8b14549a62
uv run python -m mlops_project.registry register 5907a49e09d24f678c8fb0ed265786c8
uv run python -m mlops_project.registry trace
```

The data-hash query is implemented as `tags.dvc_md5 = 'bcbdba906e4a9964cfafed8b14549a62'` in experiment `bike-demand-hw1`(ID 1). Registering results in a version change, whereas `trace` reads an existing version. The live trace is also saved in [`model-trace.json`](model-trace.json). This is a concrete example for a real value trace:

1. Alias `models:/bike-demand-random-forest@staging` resolves with
   `MlflowClient.get_model_version_by_alias` to **version 1**.
2. That version's persisted `run_id` is
   `5907a49e09d24f678c8fb0ed265786c8`. It was registered from
   `runs:/5907a49e09d24f678c8fb0ed265786c8/model`; its model source is
   `models:/m-80f9206e5fa24e00a4004db7dae9a26b`.
3. `MlflowClient.get_run` returns the winning parameters and metrics in the
   table, plus `git_commit=6b133da40ddf7aa4636611362104e20ccabdeb74`.
4. `git show 6b133da40ddf7aa4636611362104e20ccabdeb74:params.yaml` shows the
   trained settings; `git show 6b133da40ddf7aa4636611362104e20ccabdeb74:data/hour.csv.dvc`
   identifies MD5 `bcbdba906e4a9964cfafed8b14549a62`, matching the run tag.
5. The run's `data_remote_uri` is
   `s3://dvc-storage/files/md5/bc/bdba906e4a9964cfafed8b14549a62` and its
   `data_endpoint` is `http://127.0.0.1:5510`. These identify the object in the
   local Silo console on port 5511.

As an end-to-end validation step, the model was loaded via `mlflow.sklearn.load_model` for the evaluation CSV and the resulting values matched all three metrics that were logged in MLflow. The check was also implemented for the commit of the historical DVC hash pointer to the run tag. The MLflow registry command fails to set an alias if the newly registered model version has a missing or different `run_id`.

## Reflection

The most confusing error was a training command which resulted in an error message, despite the model's appearance in MLflow: inspecting the traceback revealed that the error was raised when MLflow's printed Unicode run URL was written to a Windows cp1250 console, after the model had already been saved. Configuring UTF-8 in the CLI solved this issue; completing the evaluation for this run and re-running the full pipeline confirmed the distinction between a logging failure and a training failure in this case. The data-hash guard and Git tags facilitated tracing of the resulting runs during this debugging process.

## Declared pipeline (R6) and initial tracked runs

`uv run dvc repro` completed prepare, train and evaluate.
The split at 2012-07-01 gives 13,003 training rows and 4,376 later evaluation
rows. The 12 numeric predictors explicitly selected, dates determine
ordering and the split,and ID and rental components are excluded.

With unchanged inputs, the second invocation produced:

```text
'data\hour.csv.dvc' didn't change, skipping
Stage 'prepare' didn't change, skipping
Stage 'train' didn't change, skipping
Stage 'evaluate' didn't change, skipping
Data and pipelines are up to date.
```

Changing only `train.n_estimators` from 50 to 60 in `params.yaml` produced:

```text
Stage 'prepare' didn't change, skipping
Running stage 'train':
Running stage 'evaluate':
```

There was an unchanged invocation at 60 trees and then skipped through all
stages again. The final `dvc.lock` and `metrics/metrics.json` are
committed, and metrics have `cache: false`. Source files are dependencies.
DVC tracks dataset bytes as a dependency rather than accepting `.dvc`
pointers as stage dependencies. Training independently checks that the actual
CSV matches the pointer before logging its identity.

| Trees | Run ID | RMSE | MAE | R² |
| --- | --- | --- | --- | --- |
| 50 | 8fa1c3602eab4a1d875ad616490b68af | 73.56925 | 47.82911 | 0.887859 |
| 60 | b6e7eb51f67747c0991cf0f0f74a9053 | 73.58144 | 47.85641 | 0.887822 |

Both use depth 12, minimum leaf size 2 and seed 42. These were the initial
pipeline verification runs. The completed comparison and selected settings
are documented above.

The 60-tree verification run is FINISHED and records Git commit
`1d9ece22baccc23e232ed7f6268cd3a23727ee49`, DVC MD5
`bcbdba906e4a9964cfafed8b14549a62`, and data URI
`s3://dvc-storage/files/md5/bc/bdba906e4a9964cfafed8b14549a62`.
It contains the logged sklearn model, parameters and all three metrics.
The evaluate stage resumes the training run to attach its metrics.

All eight tests passed with the project services stopped; the stack was then
restarted successfully. `dvc push` uploaded four pipeline outputs to local
Silo. No Git push was performed.

During setup, MLflow's Unicode status message exposed Windows' cp1250 console
encoding after a model had been logged. The traceback pointed to stdout
encoding, so the pipeline CLI now configures UTF-8. The first interrupted
invocation's run was evaluated by hand; a subsequent complete DVC invocation
produced the 50-tree run listed above.

## Local services (R2)

On October 15 the Compose configuration was extended using the supplied
Week 5 lab stack, which uses the same infrastructure as Week 4. No Week 5
validation functionality is included. The project keeps its existing
`bike-demand-hw1` name and `silo-data` volume so the two stored dataset
versions remain available. The existing Silo image also supplies `mcli` for the
bucket job; the project keeps its `SILO_*` variable names.

```text
docker compose up -d --wait --build
exit code: 0

SERVICE              STATE     HEALTH    EXIT CODE
mlflow               running   healthy   0
postgres             running   healthy   0
silo                 running   healthy   0
silo-create-bucket   exited              0
```

The bucket job now creates both `dvc-storage` and `mlflow-artifacts`, then
exits. MLflow waits for its successful completion and PostgreSQL readiness.
The server uses the course's pinned MLflow 3.13.0 dependencies. Actual
passwords are stored in ignored `.env`; `.env.example` contains placeholders.

## Dataset version 1

The original UCI hourly bike-sharing `data/hour.csv` is the first DVC
version. It has 17,379 data rows and 17 columns. `data/hour.csv.dvc` names
MD5 `d50bd5a6f55131e72a7bedc334e2fce1` and size `1156736` bytes. The
DVC remote is `s3://dvc-storage` on the local Silo endpoint
`http://127.0.0.1:5510`. Its object is at
`s3://dvc-storage/files/md5/d5/0bd5a6f55131e72a7bedc334e2fce1`.

The local setup was verified on October 14:

```text
docker compose up -d --wait
Container bike-demand-hw1-silo-1 Healthy
Container bike-demand-hw1-silo-create-bucket-1 Healthy

uv run dvc push
1 file pushed

docker compose exec -T silo-create-bucket mcli ls silo/dvc-storage/files/md5/d5/0bd5a6f55131e72a7bedc334e2fce1
[2026-10-14 13:10:36 UTC] 1.1MiB STANDARD 0bd5a6f55131e72a7bedc334e2fce1
```

In PowerShell, load credentials into the process before `dvc push` or
`dvc pull`. Do not print them or commit `.env`:

```powershell
$lines = Get-Content .env
$env:AWS_ACCESS_KEY_ID = (($lines | Where-Object { $_ -match '^SILO_ACCESS_KEY=' }) -replace '^SILO_ACCESS_KEY=', '')
$env:AWS_SECRET_ACCESS_KEY = (($lines | Where-Object { $_ -match '^SILO_SECRET_KEY=' }) -replace '^SILO_SECRET_KEY=', '')
uv run dvc push
Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY
```

The remote definition in `.dvc/config` contains only the URL and
endpoint, not credentials. `.dvc/config.local`, `.dvc/cache`, `.dvc/tmp`,
`.env`, and the raw CSV are Git-ignored.

### Fresh-clone pull

I cloned commit `5486412` into a new local directory with `git clone --local
--no-hardlinks . <new-directory>`, copied only the Git-ignored `.env` there,
then ran `uv sync --all-groups` and `uv run dvc pull` with the AWS
environment variables set as above. The checkout had no `data/hour.csv` before
the pull; it had `data/hour.csv.dvc`.

```text
DATA_PRESENT=False
POINTER_PRESENT=True
uv run dvc pull
A       data\hour.csv
1 file fetched and 1 file added
Get-FileHash data/hour.csv -Algorithm MD5
MD5  D50BD5A6F55131E72A7BEDC334E2FCE1
(Import-Csv data/hour.csv | Measure-Object).Count
17379
uv run pytest -q
5 passed
```

This proves a fresh checkout can download version one from the existing local
Silo service. The bucket is stored in that service's Docker volume, so a new
machine with an empty Silo volume would need the object copied or a reachable
shared Silo server.

## Dataset version 2

Version two keeps all 17,379 observations but drops `instant` (an arbitrary
row ID), `casual` and `registered`. The latter two add exactly to the target
`cnt` in every row, so retaining them would leak the answer into training. The
new CSV has 14 columns and the pointer records MD5
`bcbdba906e4a9964cfafed8b14549a62`, size `944753` bytes. Its Silo
object is `s3://dvc-storage/files/md5/bc/bdba906e4a9964cfafed8b14549a62`.

```text
uv run dvc status data/hour.csv.dvc
modified: data/hour.csv
uv run dvc add data/hour.csv
uv run dvc push
1 file pushed
```

### Switching between committed versions (R5)

Version one is commit `5486412`; version two is commit `af5f928`. The following
commands were executed, restoring version two at the end:

```text
git checkout 5486412 -- data/hour.csv.dvc
uv run dvc checkout data/hour.csv
M       data\hour.csv
Get-FileHash data/hour.csv -Algorithm MD5
D50BD5A6F55131E72A7BEDC334E2FCE1

git checkout af5f928 -- data/hour.csv.dvc
uv run dvc checkout data/hour.csv
M       data\hour.csv
Get-FileHash data/hour.csv -Algorithm MD5
BCBDBA906E4A9964CFAFED8B14549A62
```

Git selects the pointer; DVC restores the bytes named by that pointer from
its cache. Both hashes were also confirmed present in Silo after extending
the Compose stack.
