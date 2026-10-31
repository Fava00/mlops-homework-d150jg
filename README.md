# Bike Sharing Demand — MLOps HW1

This project predicts the hourly Capital Bikeshare rentals (`cnt`) by using 
calendar and weather features from the UCI Bike Sharing Dataset.
HW1 adds DVC data versioning, a reproducible Random Forest pipeline, and MLflow tracking.

This repo is **separate from the course materials**. The course repo (lectures,
labs, datasets, homework briefs) you read and do the labs in; *this* repo is your
own project, on your own dataset, and is what gets graded.

## What's here

```
pyproject.toml       project dependencies and configuration
uv.lock              locked dependency versions
compose.yaml         PostgreSQL, Silo and MLflow services
.env.example         configuration template without real credentials
src/mlops_project/   preparation, training, evaluation, provenance and registry
tests/               tests that run without the services or actual dataset
data/hour.csv.dvc    DVC pointer to the dataset
.dvc/config          DVC remote configuration without credentials
dvc.yaml             prepare → train → evaluate
dvc.lock             recorded pipeline dependency and output hashes
params.yaml          temporal split and Random Forest hyperparameters
data/                DVC dataset pointer; local restored CSV
docs/                homework evidence, data dictionary and proposal
.env.example         configuration — copy to .env
metrics/metrics.json evaluation metrics tracked in Git
```

The generic template baseline remains in `src/main.py`; the commands below
run the HW1 Random Forest pipeline.

## Quick start

Install Git, uv, and Docker with Docker Compose support. The project uses
Python 3.12 or later. Run the following commands from the repository root.

```powershell
Copy-Item .env.example .env   # fresh clone only; fill in credential placeholders
uv sync --all-groups
uv run pytest -q             # also works with the services stopped
# Activate for the grader's bare `dvc` commands (uv sync alone does not add PATH):
. .\.venv\Scripts\Activate.ps1
docker compose up -d --wait
# Load the Silo credentials for DVC (PowerShell):
$lines = Get-Content .env
$env:AWS_ACCESS_KEY_ID = (($lines | Where-Object { $_ -match '^SILO_ACCESS_KEY=' }) -replace '^SILO_ACCESS_KEY=', '')
$env:AWS_SECRET_ACCESS_KEY = (($lines | Where-Object { $_ -match '^SILO_SECRET_KEY=' }) -replace '^SILO_SECRET_KEY=', '')
uv run dvc pull
uv run dvc repro
uv run dvc repro             # unchanged stages should all be skipped
uv run dvc metrics show
uv run dvc dag
```

Prerequisites: `uv` (https://docs.astral.sh/uv/), Python 3.12+ (uv installs it),
and Docker with Compose. Every `uv run dvc ...` command below is equivalent
to `dvc ...` after activating this project's virtual environment.

For Bash, activate with `source .venv/bin/activate`. After filling in `.env`,
load the Silo credentials into the terminal before `dvc pull`:

```bash
set -a
source .env
set +a
export AWS_ACCESS_KEY_ID="$SILO_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SILO_SECRET_KEY"
```

## HW1 pipeline

With the services running and the dataset restored, run `uv run dvc repro`.
The three stages can also be run by hand:

```powershell
uv run python -m mlops_project.pipeline prepare
uv run python -m mlops_project.pipeline train
uv run python -m mlops_project.pipeline evaluate
```

params.yaml is used to select the split date and Random Forest hyperparameters.
Training uses all observations before 1 July 2012, and evaluation uses all
observations from that moment on. This is a chronological holdout, so its
results represent that specific future period. The pipeline is using the 12
calendar / weather predictors, and not using the date, row ID, and the
two components of the target. The date is only needed to make the split.

Training logs the parameters, the model, Git commit, verified DVC MD5, and Silo
object URI to the bike-demand-hw1 experiment. Evaluation appends the RMSE, MAE, and
R2 to that same run and writes metrics/metrics.json. Run both to complete an
experiment. uv run dvc metrics show will display the local metrics.
The previous generic template entry point is preserved; use the commands above
for the HW1 pipeline.

## Experiments and registered model

[docs/hw1.md](docs/hw1.md) compares 4 parameter configurations. The chosen model uses 100 trees, depth 16, and minimum leaf size 1. It achieves evaluation RMSE 71.59137 rentals/hour. Note this was the later period used for model selection, so it is not an independent final-test result.

The local MLflow registry alias is models:/bike-demand-random-forest@staging (version 1). Find all runs in this registry alias, and all other runs on this version of the data (bcbdba906e4a9964cfafed8b14549a62), via:

```powershell
uv run python -m mlops_project.registry trace
uv run python -m mlops_project.registry runs-for-data bcbdba906e4a9964cfafed8b14549a62
```

Use uv run python -m mlops_project.registry register <run-id> to register a new run as a model version, and the registry alias "staging" will be updated after verifying its source run link. The trace and comparison output are persisted as evidence, but the real-time model registry state is stored in the local PostgreSQL and Silo volumes.


## HW1: services and dataset storage

The UCI hourly bike-sharing data is used to predict cnt, the number of hourly rentals. The raw CSV is not versioned via git in data/hour.csv, but its path is tracked by DVC at [data/hour.csv.dvc](data/hour.csv.dvc): MD5 bcbdba906e4a9964cfafed8b14549a62, size **944,753 bytes**, **17,379 data rows and 14 columns**. Version 1 of this tracked pointer file pointed to the original 17 column CSV; version 2 removes the columns instant, casual, and registered from consideration for training.

Copy .env.example to .env and replace the Silo and PostgreSQL credential placeholders with unique values. A URL-safe PostgreSQL password is required, as described in .env.example. Then run docker compose up -d --wait. The Compose build builds the tracking server from mlflow.Dockerfile only on the first run. The long-running containers should come up healthy, and the short-lived silo-create-bucket container should exit successfully with code 0.

| Service | Host port | Address |
| --- | --- | --- |
| MLflow | 5500 | http://localhost:5500 |
| Silo S3 API | 5510 | http://localhost:5510 |
| Silo console | 5511 | http://localhost:5511 |
| PostgreSQL | 5532 | localhost:5532 |

The Compose project is given an explicit name, bike-demand-hw1. Run docker compose down to stop it, and keep the data and experiments stored in the volumes. docker compose down -v will destroy the storage volumes, including all the DVC objects and MLflow runs.

For dvc commands, set AWS_ACCESS_KEY_ID from SILO_ACCESS_KEY, and AWS_SECRET_ACCESS_KEY from SILO_SECRET_KEY in the git-ignored .env, then run uv run dvc push or uv run dvc pull. See [docs/hw1.md](docs/hw1.md) for the full set of PowerShell commands and verification output. No credentials are stored in .dvc/config.

If you change SILO_API_PORT, update the local DVC endpoint via uv run dvc remote modify --local silo endpointurl http://127.0.0.1:<port>. If you change MLFLOW_PORT, update MLFLOW_TRACKING_URI in .env accordingly. The default committed endpoint is port 5510.
