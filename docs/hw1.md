# HW1 evidence

## Final local fresh-clone verification

On 15 October 2026, commit `42034e7` was cloned from this local repository
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

With this project's services stopped using `docker compose stop` in the
original checkout, `uv run pytest -q` in the fresh clone reported
`11 passed in 4.66s`. The services were restarted afterwards.

The first final-clone check exposed an unnecessary evaluation rerun: Python
wrote CRLF metrics on Windows while Git checked out LF. The metrics writer
now explicitly emits UTF-8 with LF, and the repeated fresh-clone check above
confirms byte-identical outputs. The final verification commit changes only
this evidence, not the validated code or pipeline state.

These checks use the existing local Silo and MLflow storage. They do not
establish access from another machine with empty Docker volumes. Grading
access and repository submission remain to be arranged; no Git push was run.

## Four-setting comparison and registry (R7–R9)

All four settings use the same version-two dataset, split date 2012-07-01,
13,003 earlier training rows, 4,376 later evaluation rows, and random seed 42.
RMSE in rentals/hour is the primary selection metric because it penalizes
large demand errors. The results queried from the local MLflow server are:

| Trees | Maximum depth | Minimum leaf size | Run ID | RMSE | MAE | R² |
| --- | --- | --- | --- | --- | --- | --- |
| 50 | 12 | 2 | 8fa1c3602eab4a1d875ad616490b68af | 73.56925 | 47.82911 | 0.887859 |
| 60 | 12 | 2 | b6e7eb51f67747c0991cf0f0f74a9053 | 73.58144 | 47.85641 | 0.887822 |
| **100** | **16** | **1** | **5907a49e09d24f678c8fb0ed265786c8** | **71.59137** | **46.27602** | **0.893808** |
| 100 | 8 | 4 | 2823b459ab054a628cff67e003b844ac | 89.81294 | 60.03313 | 0.832872 |

The depth-16 model wins on RMSE and also has the lowest MAE. Increasing the
original model from 50 to 60 trees made almost no difference, while the
shallower forest had substantially larger errors. This small comparison does
not establish a global optimum. Because the later period was used to select
the model, its score is a selection-period score, not an untouched final-test
estimate. A later deployment assessment should use another future period or
rolling temporal evaluation. Observed weather covariates also mean this is
conditional hourly demand estimation, not a demonstrated advance weather forecast.

The winning settings are restored in `params.yaml`, `dvc.lock`, and the local
metrics. DVC restored the matching cached outputs without creating a duplicate
training run. The full data-hash query output is saved in
[`runs-for-data.json`](runs-for-data.json), including the earlier duplicate
50-tree run from the console-encoding investigation.

```powershell
uv run python -m mlops_project.registry runs-for-data bcbdba906e4a9964cfafed8b14549a62
uv run python -m mlops_project.registry register 5907a49e09d24f678c8fb0ed265786c8
uv run python -m mlops_project.registry trace
```

The query uses `tags.dvc_md5 = 'bcbdba906e4a9964cfafed8b14549a62'` in
experiment `bike-demand-hw1` (ID 1). Registering is an explicit action that
creates a new version; `trace` is read-only. The live trace is also saved in
[`model-trace.json`](model-trace.json). It walks these real values:

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

As an end-to-end check, loading `models:/bike-demand-random-forest@staging`
with `mlflow.sklearn.load_model` and predicting the evaluation CSV reproduced
all three recorded metrics. The historical commit's DVC pointer was also
checked against the run tag. The registry command refuses to set an alias if
the newly registered version has a missing or different `run_id`.

## Reflection

The most confusing failure was a training command returning an error even
though its model already appeared in MLflow. Reading the traceback showed
that the failure occurred while printing MLflow's Unicode run link to a
Windows cp1250 console, after the model was uploaded. Configuring UTF-8 in
the CLI fixed it; completing evaluation for that run and reproducing the
pipeline confirmed the distinction between a logging failure and a model
training failure. The data-hash guard and Git tags helped keep the resulting
runs traceable through this debugging process.

## Declared pipeline (R6) and initial tracked runs

On 15 October 2026, `uv run dvc repro` completed prepare, train and evaluate.
The split at 2012-07-01 gives 13,003 training rows and 4,376 later evaluation
rows. The 12 numeric/coded predictors are selected explicitly; dates determine
ordering and the split, while ID and rental components are excluded.

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

An unchanged invocation at 60 trees then skipped every stage again. The final
`dvc.lock` and `metrics/metrics.json` are committed; metrics have `cache: false`.
Source files are dependencies. DVC tracks dataset bytes as a dependency rather
than accepting `.dvc` pointers as stage dependencies. Training independently
checks that the actual CSV matches the pointer before logging its identity.

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

On 15 October 2026 the Compose configuration was extended using the supplied
Week 5 lab stack, which uses the same infrastructure as Week 4. No Week 5
validation functionality is included. The project keeps its existing
`bike-demand-hw1` name and `silo-data` volume so the two stored dataset versions
remain available. The existing Silo image also supplies `mcli` for the bucket
job; the project keeps its `SILO_*` variable names.

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
The server uses the course's pinned MLflow 3.13.0 dependencies. Actual passwords
are stored in ignored `.env`; `.env.example` contains placeholders.

## Dataset version 1

The original UCI hourly bike-sharing `data/hour.csv` is the first DVC version.
It has 17,379 data rows and 17 columns. `data/hour.csv.dvc` names MD5
`d50bd5a6f55131e72a7bedc334e2fce1` and size `1156736` bytes. The DVC
remote is `s3://dvc-storage` on the local Silo endpoint
`http://127.0.0.1:5510`. Its object is at
`s3://dvc-storage/files/md5/d5/0bd5a6f55131e72a7bedc334e2fce1`.

The local setup was verified on 14 October 2026:

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

The remote definition in `.dvc/config` contains only the URL and endpoint, not
credentials. `.dvc/config.local`, `.dvc/cache`, `.dvc/tmp`, `.env`, and the raw
CSV are Git-ignored.

### Fresh-clone pull

I cloned commit `5486412` into a new local directory with `git clone --local
--no-hardlinks . <new-directory>`, copied only the Git-ignored `.env` there,
then ran `uv sync --all-groups` and `uv run dvc pull` with the AWS environment
variables set as above. The checkout had no `data/hour.csv` before the pull;
it had `data/hour.csv.dvc`.

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

Version two keeps all 17,379 observations but drops `instant` (an arbitrary row
ID), `casual` and `registered`. The latter two add exactly to the target `cnt`
in every row, so retaining them would leak the answer into training. The new
CSV has 14 columns and the pointer records MD5
`bcbdba906e4a9964cfafed8b14549a62`, size `944753` bytes. Its Silo object
is `s3://dvc-storage/files/md5/bc/bdba906e4a9964cfafed8b14549a62`.

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

Git selects the pointer; DVC restores the bytes named by that pointer from its
cache. Both hashes were also confirmed present in Silo after extending the
Compose stack.
